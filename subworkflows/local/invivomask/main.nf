include { BET } from '../bet/main.nf'
include { MOUSE_ALIGNANATMASK } from '../../../modules/local/mouse/alignanatmask/main.nf'
include { MOUSE_VALIDATEINVIVOMASK } from '../../../modules/local/mouse/alignanatmask/validatemask.nf'

workflow INVIVO_MASK {
    take:
        b0
        anatomy
        register_anat
        validator

    main:
        subjects = b0.join(anatomy, remainder: true, failOnDuplicate: true)
            .map { meta, reference, anat ->
                if (!reference) error "${meta.id}: anatomical input has no matching DWI b0"
                [meta, reference, anat ?: []]
            }

        BET(subjects.map { meta, reference, anat -> [meta, anat ?: reference] })
        masks = subjects.join(BET.out.mask, failOnMismatch: true, failOnDuplicate: true)
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
