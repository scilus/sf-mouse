include { INVIVO_MASK } from '../../subworkflows/local/invivomask/main.nf'

workflow {
    def input = file(params.input)
    def validator = file("${projectDir}/../../modules/local/mouse/alignanatmask/validate_grids.py")
    def b0s = [
        [[id: 'anatomy'], input.resolve('b0_anatomy.nii.gz')],
        [[id: 'fallback'], input.resolve('b0_fallback.nii.gz')]
    ]
    def anatomies = [[[id: 'anatomy'], input.resolve('anat.nii.gz')]]
    if (params.scenario == 'duplicate-anatomy') {
        anatomies << [[id: 'anatomy'], input.resolve('duplicate.nii.gz')]
    } else if (params.scenario == 'duplicate-b0') {
        b0s << [[id: 'fallback'], input.resolve('duplicate.nii.gz')]
    } else if (params.scenario == 'orphan-anatomy') {
        anatomies << [[id: 'orphan'], input.resolve('duplicate.nii.gz')]
    } else if (params.scenario == 'no-anatomy') {
        anatomies = []
    }
    INVIVO_MASK(Channel.fromList(b0s), Channel.fromList(anatomies), true, validator)
    INVIVO_MASK.out.mask.view { meta, mask -> "RESULT ${meta.id} ${mask}" }
}
