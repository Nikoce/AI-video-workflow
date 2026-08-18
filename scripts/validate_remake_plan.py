#!/usr/bin/env python3
"""Validate a platform-neutral reference-video remake plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ALLOWED_MODES = {"analysis_only", "prompt_package", "variant_package", "execute"}
GENERATION_STATUSES = {"planned", "generating", "generated", "accepted", "failed"}
REFERENCE_STATUSES = {"planned", "ready", "rejected"}
TAIL_STATUSES = {"planned", "ready", "rejected"}
TRANSITIONS = {"opening", "continuous", "hard_cut"}
OUTPUT_MODES = {"direct_variant_prompts", "matrix_only"}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def is_placeholder(value: str) -> bool:
    return value.startswith("<") and value.endswith(">")


def same_pointer(left: Any, right: Any) -> bool:
    return bool(text(left)) and text(left).casefold() == text(right).casefold()


def pointer_accessible(pointer: Any, warnings: list[str], context: str) -> bool:
    value = text(pointer)
    if not value or is_placeholder(value):
        return False

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "asset", "node", "project"}:
        warnings.append(f"{context} uses a remote or executor asset pointer; verify it externally.")
        return True

    return Path(value).expanduser().is_file()


def validate(plan: dict[str, Any], phase: str, target_segment_id: str | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    def error(message: str) -> None:
        errors.append(message)

    def warn(message: str) -> None:
        warnings.append(message)

    if plan.get("schema_version") != 3:
        error("schema_version must be 3.")

    mode = text(plan.get("workflow_mode"))
    if mode not in ALLOWED_MODES:
        error(f"workflow_mode must be one of: {', '.join(sorted(ALLOWED_MODES))}.")
    generation_plan_required = mode in {"prompt_package", "variant_package", "execute"}

    settings = as_dict(plan.get("settings"))
    try:
        max_segment_seconds = float(settings.get("max_segment_seconds"))
    except (TypeError, ValueError):
        max_segment_seconds = 0.0
        error("settings.max_segment_seconds must be numeric.")
    if not 0 < max_segment_seconds <= 15:
        error("settings.max_segment_seconds must be greater than 0 and no more than 15.")
    if text(settings.get("generation_mode")) != "serial_tail_frame_chain":
        error("settings.generation_mode must be serial_tail_frame_chain.")
    output_mode = text(settings.get("output_mode"))
    if output_mode and output_mode not in OUTPUT_MODES:
        error("settings.output_mode must be direct_variant_prompts or matrix_only.")
    if mode == "variant_package" and not output_mode:
        warn("settings.output_mode is empty; defaulting to direct_variant_prompts.")
    if not text(settings.get("ratio")):
        warn("settings.ratio is empty.")
    if not text(settings.get("resolution")):
        warn("settings.resolution is empty.")

    execution = as_dict(plan.get("execution"))
    adapter = as_dict(execution.get("adapter"))
    capabilities_verified = adapter.get("capabilities_verified") is True
    if mode == "execute" and not capabilities_verified:
        error("execute mode requires a verified execution adapter.")
    if phase in {"pre-generate", "final"} and mode != "execute":
        error(f"{phase} validation requires workflow_mode execute.")
    if phase in {"pre-generate", "final"}:
        if adapter.get("supports_scene_reference") is not True:
            error("Execution adapter must support scene reference images.")
        if adapter.get("supports_start_frame") is not True:
            error("Execution adapter must support an explicit start frame.")
        if not text(adapter.get("verification_evidence")) or is_placeholder(text(adapter.get("verification_evidence"))):
            error("Execution adapter requires concrete verification_evidence.")

    adapter_max = adapter.get("max_duration_seconds")
    if capabilities_verified and adapter_max is not None:
        try:
            adapter_max_value = float(adapter_max)
            if adapter_max_value <= 0:
                error("execution.adapter.max_duration_seconds must be positive.")
            elif max_segment_seconds > adapter_max_value:
                error("settings.max_segment_seconds exceeds the verified adapter duration limit.")
        except (TypeError, ValueError):
            error("execution.adapter.max_duration_seconds must be numeric or null.")

    supported_ratios = [text(item) for item in as_list(adapter.get("supported_ratios"))]
    supported_resolutions = [text(item) for item in as_list(adapter.get("supported_resolutions"))]
    if capabilities_verified and supported_ratios and text(settings.get("ratio")) not in supported_ratios:
        error("settings.ratio is not supported by the verified execution adapter.")
    if capabilities_verified and supported_resolutions and text(settings.get("resolution")) not in supported_resolutions:
        error("settings.resolution is not supported by the verified execution adapter.")

    source_dialogue = as_list(plan.get("source_dialogue"))
    source_dialogue_ids = [text(item.get("id")) for item in source_dialogue if isinstance(item, dict)]
    for dialogue_id in sorted({item for item in source_dialogue_ids if source_dialogue_ids.count(item) > 1}):
        error(f"Duplicate source dialogue id: {dialogue_id}")

    core_script = as_dict(plan.get("core_script"))
    variant_policy = as_dict(plan.get("variant_policy"))
    variants = as_list(plan.get("variants"))
    variants_requested = mode == "variant_package" or "variants" in plan
    if variants_requested:
        core_id = text(core_script.get("id"))
        if not core_id:
            error("Variant plans require core_script.id.")
        if core_script.get("frozen") is not True:
            error("Variant plans require core_script.frozen=true.")

        beat_ids: list[str] = []
        for raw_beat in as_list(core_script.get("beats")):
            beat = as_dict(raw_beat)
            beat_id = text(beat.get("id"))
            if not beat_id:
                error("Every core_script beat must have a non-empty id.")
            elif beat_id in beat_ids:
                error(f"Duplicate core_script beat id: {beat_id}")
            else:
                beat_ids.append(beat_id)
        if not beat_ids:
            error("Variant plans require at least one core_script beat.")

        core_dialogue_ids = [text(item) for item in as_list(core_script.get("dialogue_ids"))]
        if len(core_dialogue_ids) != len(set(core_dialogue_ids)):
            error("core_script.dialogue_ids must be unique.")
        for dialogue_id in core_dialogue_ids:
            if dialogue_id not in source_dialogue_ids:
                error(f"core_script references unknown dialogue id: {dialogue_id}")
        dialogue_texts = as_dict(core_script.get("dialogue_texts"))
        if set(dialogue_texts) != set(core_dialogue_ids):
            error("core_script.dialogue_texts keys must exactly match core_script.dialogue_ids.")
        for dialogue_id in core_dialogue_ids:
            if not text(dialogue_texts.get(dialogue_id)):
                error(f"core_script.dialogue_texts requires non-empty text for {dialogue_id}.")

        invariants = [text(item) for item in as_list(core_script.get("invariants"))]
        if not invariants:
            error("Variant plans require at least one core_script invariant.")

        try:
            variant_count = int(variant_policy.get("count"))
            if variant_count <= 0:
                error("variant_policy.count must be positive.")
        except (TypeError, ValueError):
            variant_count = 0
            error("variant_policy.count must be an integer.")

        allowed_axes = [text(item) for item in as_list(variant_policy.get("allowed_axes"))]
        forbidden_axes = [text(item) for item in as_list(variant_policy.get("forbidden_axes"))]
        if len(allowed_axes) != len(set(allowed_axes)):
            error("variant_policy.allowed_axes must be unique.")
        if len(forbidden_axes) != len(set(forbidden_axes)):
            error("variant_policy.forbidden_axes must be unique.")
        overlap = sorted(set(allowed_axes) & set(forbidden_axes))
        if overlap:
            error(f"Variant axes cannot be both allowed and forbidden: {', '.join(overlap)}")

        max_changed_axes = variant_policy.get("max_changed_axes_per_variant")
        try:
            max_changed_axes_value = int(max_changed_axes) if max_changed_axes is not None else None
            if max_changed_axes_value is not None and max_changed_axes_value <= 0:
                error("variant_policy.max_changed_axes_per_variant must be positive or null.")
        except (TypeError, ValueError):
            max_changed_axes_value = None
            error("variant_policy.max_changed_axes_per_variant must be an integer or null.")

        if not variants:
            error("Variant plans require at least one variant.")
        if variant_count and variant_count != len(variants):
            error("variant_policy.count must equal the number of variants.")

        required_core_ids = set(beat_ids + core_dialogue_ids)
        variant_ids: set[str] = set()
        allowed_statuses = {"planned", "approved", "generated", "accepted", "failed"}
        for raw_variant in variants:
            variant = as_dict(raw_variant)
            variant_id = text(variant.get("id"))
            if not variant_id:
                error("Every variant must have a non-empty id.")
                continue
            if variant_id in variant_ids:
                error(f"Duplicate variant id: {variant_id}")
            variant_ids.add(variant_id)
            if text(variant.get("source_core_script_id")) != core_id:
                error(f"Variant {variant_id} must reference core_script {core_id}.")

            changed_axes = [text(item) for item in as_list(variant.get("changed_axes"))]
            if not changed_axes:
                error(f"Variant {variant_id} must declare changed_axes.")
            if len(changed_axes) != len(set(changed_axes)):
                error(f"Variant {variant_id} changed_axes must be unique.")
            unknown_axes = sorted(set(changed_axes) - set(allowed_axes))
            if unknown_axes:
                error(f"Variant {variant_id} uses axes outside allowed_axes: {', '.join(unknown_axes)}")
            forbidden_used = sorted(set(changed_axes) & set(forbidden_axes))
            if forbidden_used:
                error(f"Variant {variant_id} uses forbidden axes: {', '.join(forbidden_used)}")
            if max_changed_axes_value is not None and len(changed_axes) > max_changed_axes_value:
                error(f"Variant {variant_id} exceeds max_changed_axes_per_variant.")
            if not as_dict(variant.get("delta")):
                error(f"Variant {variant_id} requires a delta object.")
            if as_dict(variant.get("dialogue_overrides")):
                error(f"Variant {variant_id} cannot override dialogue while core_script is frozen.")
            preserved = [text(item) for item in as_list(variant.get("preserved_core_ids"))]
            if set(preserved) != required_core_ids:
                missing = sorted(required_core_ids - set(preserved))
                extra = sorted(set(preserved) - required_core_ids)
                details = []
                if missing:
                    details.append(f"missing {', '.join(missing)}")
                if extra:
                    details.append(f"unknown {', '.join(extra)}")
                error(f"Variant {variant_id} must preserve every core id ({'; '.join(details)}).")
            if not text(variant.get("generation_prompt")):
                error(f"Variant {variant_id} requires a complete generation_prompt.")
            status = text(variant.get("status"))
            if status not in allowed_statuses:
                error(f"Variant {variant_id} has an invalid status.")

    shots = as_list(plan.get("shots"))
    if not shots:
        error("Plan must contain at least one shot.")
    shot_by_id: dict[str, dict[str, Any]] = {}
    mapped_dialogue_ids: list[str] = []
    for raw_shot in shots:
        shot = as_dict(raw_shot)
        shot_id = text(shot.get("id"))
        if not shot_id:
            error("Every shot must have a non-empty id.")
            continue
        if shot_id in shot_by_id:
            error(f"Duplicate shot id: {shot_id}")
            continue
        shot_by_id[shot_id] = shot
        try:
            if float(shot.get("duration_seconds")) <= 0:
                error(f"Shot {shot_id} must have a positive duration_seconds.")
        except (TypeError, ValueError):
            error(f"Shot {shot_id} duration_seconds must be numeric.")

        for raw_dialogue in as_list(shot.get("remake_dialogue")):
            dialogue = as_dict(raw_dialogue)
            source_id = text(dialogue.get("source_id"))
            if not source_id:
                error(f"Shot {shot_id} contains remake dialogue without source_id.")
                continue
            mapped_dialogue_ids.append(source_id)
            if source_id not in source_dialogue_ids:
                error(f"Shot {shot_id} maps unknown source dialogue id: {source_id}")
            if not text(dialogue.get("text")):
                error(f"Shot {shot_id} maps {source_id} to empty dialogue text.")

    omission_ids: list[str] = []
    for raw_omission in as_list(plan.get("omissions")):
        omission = as_dict(raw_omission)
        source_id = text(omission.get("source_id"))
        if source_id not in source_dialogue_ids:
            error(f"Omission references unknown source dialogue id: {source_id}")
        if omission.get("user_confirmed") is not True:
            error(f"Omission for {source_id} is not explicitly user-confirmed.")
        if not text(omission.get("reason")):
            error(f"Omission for {source_id} requires a reason.")
        omission_ids.append(source_id)

    if generation_plan_required:
        for source_id in source_dialogue_ids:
            count = mapped_dialogue_ids.count(source_id) + omission_ids.count(source_id)
            if count == 0:
                error(f"Source dialogue {source_id} is neither mapped nor explicitly omitted.")
            elif count > 1:
                error(f"Source dialogue {source_id} is mapped or omitted more than once.")

    references = as_list(plan.get("scene_references"))
    if generation_plan_required and not references:
        error("Generation plans require at least one full-scene reference image plan.")
    reference_by_id: dict[str, dict[str, Any]] = {}
    reference_by_scene: dict[str, dict[str, Any]] = {}
    for raw_reference in references:
        reference = as_dict(raw_reference)
        reference_id = text(reference.get("id"))
        scene_id = text(reference.get("scene_id"))
        if not reference_id or not scene_id:
            error("Every scene reference must have non-empty id and scene_id.")
            continue
        if reference_id in reference_by_id:
            error(f"Duplicate scene reference id: {reference_id}")
            continue
        if scene_id in reference_by_scene:
            error(f"Scene {scene_id} has more than one active reference image.")
            continue
        reference_by_id[reference_id] = reference
        reference_by_scene[scene_id] = reference
        if text(reference.get("status")) not in REFERENCE_STATUSES:
            error(f"Scene reference {reference_id} has an invalid status.")
        if not text(reference.get("generation_prompt")):
            error(f"Scene reference {reference_id} requires a generation_prompt.")

    segments = as_list(plan.get("segments"))
    if generation_plan_required and not segments:
        error("Generation plans require at least one segment.")
    segment_by_id: dict[str, dict[str, Any]] = {}
    segmented_shot_ids: list[str] = []

    for raw_segment in segments:
        segment = as_dict(raw_segment)
        segment_id = text(segment.get("id"))
        continuity = as_dict(segment.get("continuity"))
        if not segment_id:
            error("Every segment must have a non-empty id.")
            continue
        if segment_id in segment_by_id:
            error(f"Duplicate segment id: {segment_id}")
            continue
        segment_by_id[segment_id] = segment

        try:
            if int(segment.get("sequence_index")) <= 0:
                error(f"Segment {segment_id} must have a positive sequence_index.")
        except (TypeError, ValueError):
            error(f"Segment {segment_id} sequence_index must be numeric.")

        if text(segment.get("generation_status")) not in GENERATION_STATUSES:
            error(f"Segment {segment_id} has an invalid generation_status.")
        if text(continuity.get("tail_frame_status")) not in TAIL_STATUSES:
            error(f"Segment {segment_id} has an invalid tail_frame_status.")
        if text(continuity.get("transition_from_previous")) not in TRANSITIONS:
            error(f"Segment {segment_id} has an invalid transition_from_previous.")

        computed_duration = 0.0
        shot_bgms: set[str] = set()
        for shot_id_value in as_list(segment.get("shot_ids")):
            shot_id = text(shot_id_value)
            if shot_id not in shot_by_id:
                error(f"Segment {segment_id} references unknown shot id: {shot_id}")
                continue
            segmented_shot_ids.append(shot_id)
            try:
                computed_duration += float(shot_by_id[shot_id].get("duration_seconds"))
            except (TypeError, ValueError):
                pass
            bgm = text(as_dict(shot_by_id[shot_id].get("audio")).get("bgm"))
            if bgm:
                shot_bgms.add(bgm)

        try:
            declared_duration = float(segment.get("duration_seconds"))
            if abs(declared_duration - computed_duration) > 0.25:
                error(f"Segment {segment_id} duration differs from its shots by more than 0.25s.")
            if declared_duration > max_segment_seconds:
                error(f"Segment {segment_id} exceeds the configured segment limit.")
        except (TypeError, ValueError):
            error(f"Segment {segment_id} duration_seconds must be numeric.")

        if len(shot_bgms) > 1:
            error(f"Segment {segment_id} combines shots with conflicting BGM requirements.")
        segment_bgm = text(as_dict(segment.get("audio")).get("bgm"))
        if len(shot_bgms) == 1 and segment_bgm not in shot_bgms:
            error(f"Segment {segment_id} BGM conflicts with its shot-level requirement.")

        reference_id = text(continuity.get("scene_reference_id"))
        if reference_id not in reference_by_id:
            error(f"Segment {segment_id} references unknown scene reference id: {reference_id}")
        elif text(reference_by_id[reference_id].get("scene_id")) != text(segment.get("scene_id")):
            error(f"Segment {segment_id} scene_id does not match scene reference {reference_id}.")

        if text(continuity.get("tail_frame_status")) == "ready" and text(segment.get("generation_status")) != "accepted":
            error(f"Segment {segment_id} cannot have a ready tail frame before acceptance.")

    if segments:
        for shot_id in shot_by_id:
            count = segmented_shot_ids.count(shot_id)
            if count == 0:
                error(f"Shot {shot_id} is not assigned to any segment.")
            elif count > 1:
                error(f"Shot {shot_id} is assigned to more than one segment.")

    def sequence_value(segment: dict[str, Any]) -> int:
        try:
            return int(segment.get("sequence_index"))
        except (TypeError, ValueError):
            return 10**9

    ordered_segments = sorted((as_dict(item) for item in segments), key=sequence_value)
    for index, segment in enumerate(ordered_segments):
        segment_id = text(segment.get("id"))
        continuity = as_dict(segment.get("continuity"))
        expected_index = index + 1
        if sequence_value(segment) != expected_index:
            error(f"Segment sequence_index must be unique and contiguous; expected {expected_index} at {segment_id}.")

        transition = text(continuity.get("transition_from_previous"))
        if index == 0:
            if transition != "opening":
                error(f"First segment {segment_id} must use opening transition.")
            if text(continuity.get("previous_segment_id")):
                error(f"First segment {segment_id} cannot reference a previous segment.")
            if text(continuity.get("start_frame_pointer")):
                error(f"First segment {segment_id} cannot inherit a start frame.")
            continue

        previous = ordered_segments[index - 1]
        previous_id = text(previous.get("id"))
        previous_continuity = as_dict(previous.get("continuity"))
        if text(continuity.get("previous_segment_id")) != previous_id:
            error(f"Segment {segment_id} must reference immediately preceding segment {previous_id}.")

        same_scene = text(segment.get("scene_id")) == text(previous.get("scene_id"))
        if same_scene:
            if transition != "continuous":
                error(f"Same-scene segment {segment_id} must use continuous tail-frame handoff.")
            if not same_pointer(continuity.get("start_frame_pointer"), previous_continuity.get("tail_frame_pointer")):
                error(f"Segment {segment_id} start frame must equal segment {previous_id} tail frame.")
            if text(continuity.get("scene_reference_id")) != text(previous_continuity.get("scene_reference_id")):
                error(f"Same-scene segment {segment_id} must reuse segment {previous_id} scene reference.")
        else:
            if transition != "hard_cut":
                error(f"New-scene segment {segment_id} must declare hard_cut.")
            if not text(continuity.get("transition_reason")):
                error(f"Hard cut before segment {segment_id} requires a transition_reason.")
            if text(continuity.get("start_frame_pointer")):
                error(f"Hard-cut segment {segment_id} must not inherit the previous scene tail frame.")

        if text(segment.get("generation_status")) in {"generating", "generated", "accepted"}:
            if text(previous.get("generation_status")) != "accepted":
                error(f"Segment {segment_id} cannot start before segment {previous_id} is accepted.")
            if same_scene and text(previous_continuity.get("tail_frame_status")) != "ready":
                error(f"Segment {segment_id} cannot start before segment {previous_id} tail frame is ready.")

    if phase == "pre-generate":
        if not target_segment_id:
            error("pre-generate phase requires --segment-id.")
        elif target_segment_id not in segment_by_id:
            error(f"Pre-generate target segment does not exist: {target_segment_id}")
        else:
            target = segment_by_id[target_segment_id]
            continuity = as_dict(target.get("continuity"))
            reference_id = text(continuity.get("scene_reference_id"))
            reference = reference_by_id.get(reference_id)
            if reference:
                if text(reference.get("status")) != "ready":
                    error(f"Segment {target_segment_id} scene reference {reference_id} is not ready.")
                if not pointer_accessible(reference.get("asset_pointer"), warnings, f"Scene reference {reference_id}"):
                    error(f"Segment {target_segment_id} scene reference asset is not accessible.")

            if text(continuity.get("transition_from_previous")) == "continuous":
                previous_id = text(continuity.get("previous_segment_id"))
                previous = segment_by_id.get(previous_id)
                if previous:
                    previous_continuity = as_dict(previous.get("continuity"))
                    if text(previous.get("generation_status")) != "accepted":
                        error(f"Segment {target_segment_id} requires accepted previous segment {previous_id}.")
                    if text(previous_continuity.get("tail_frame_status")) != "ready":
                        error(f"Segment {target_segment_id} requires ready tail frame from {previous_id}.")
                    if not pointer_accessible(continuity.get("start_frame_pointer"), warnings, f"Segment {target_segment_id} start frame"):
                        error(f"Segment {target_segment_id} start frame is not accessible.")

    if phase == "final":
        for reference_id, reference in reference_by_id.items():
            if text(reference.get("status")) != "ready":
                error(f"Final validation requires ready scene reference {reference_id}.")
            if not pointer_accessible(reference.get("asset_pointer"), warnings, f"Scene reference {reference_id}"):
                error(f"Final validation cannot access scene reference {reference_id}.")
        for segment_id, segment in segment_by_id.items():
            if text(segment.get("generation_status")) != "accepted":
                error(f"Final validation requires accepted segment {segment_id}.")
            if not pointer_accessible(segment.get("output_video_pointer"), warnings, f"Segment {segment_id} output"):
                error(f"Final validation cannot access output video for segment {segment_id}.")

    return {
        "valid": not errors,
        "phase": phase,
        "segment_id": target_segment_id,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Remake plan JSON path")
    parser.add_argument("--phase", choices=["plan", "pre-generate", "final"], default="plan")
    parser.add_argument("--segment-id", help="Target segment for pre-generate validation")
    args = parser.parse_args()

    path = Path(args.path).expanduser().resolve()
    if not path.is_file():
        parser.error(f"Plan does not exist: {path}")
    plan = json.loads(path.read_text(encoding="utf-8"))
    result = validate(plan, args.phase, args.segment_id)
    result["plan_path"] = str(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
