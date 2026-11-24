include { BET } from '../bet/main.nf'
include { MOUSE_ALIGNANATMASK } from '../../../modules/local/mouse/alignanatmask/main.nf'
include { MOUSE_VALIDATEINVIVOMASK } from '../../../modules/local/mouse/alignanatmask/validatemask.nf'

workflow INVIVO_MASK {
    take:
        b0
        anatomy
        provided_mask
        register_anat
        validator

    main:
        subjects = b0.join(anatomy, remainder: true, failOnDuplicate: true)
            .map { meta, reference, anat ->
                if (!reference) error "${meta.id}: anatomical input has no matching DWI b0"
                [meta, reference, anat ?: []]
            }
            .join(provided_mask, remainder: true, failOnDuplicate: true)
            .map { row ->
                if (row.size() == 3 && !row[1]) {
                    error "${row[0].id}: provided mask has no matching DWI b0"
                }
                [row[0], row[1], row[2], row[3] ?: []]
            }
            .branch { meta, reference, anat, mask ->
                provided: mask
                generate: true
            }

        BET(subjects.generate.map { meta, reference, anat, _mask -> [meta, anat ?: reference] })
        generated_masks = subjects.generate.join(BET.out.mask, failOnMismatch: true, failOnDuplicate: true)
            .map { meta, reference, anat, _provided_mask, mask -> [meta, reference, anat, mask] }
        provided_masks = subjects.provided.map { meta, reference, anat, mask -> [meta, reference, anat, mask] }
        masks = generated_masks.mix(provided_masks)
            .branch { meta, reference, anat, mask ->
                anatomical: anat
                dwi: true
            }
        MOUSE_ALIGNANATMASK(masks.anatomical, register_anat, validator)
        MOUSE_VALIDATEINVIVOMASK(
            masks.dwi.map { meta, reference, anat, mask -> [meta, reference, mask] }, validator)
        result = MOUSE_ALIGNANATMASK.out.mask.mix(MOUSE_VALIDATEINVIVOMASK.out.mask)

    emit:
        mask = result
}
