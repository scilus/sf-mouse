include { MOUSE_ALIGNANATMASK; parse_invivo_register_anat } from '../../modules/local/mouse/alignanatmask/main.nf'

workflow {
    def register = parse_invivo_register_anat(params.register)
    println "REGISTER ${register}"
    def image = file(params.input)
    def validator = file("${projectDir}/../../modules/local/mouse/alignanatmask/validate_grids.py")
    def subjects = ['same', 'different'].collect { name ->
        [[id: name], image.resolve("${name}_b0.nii.gz"), image.resolve("${name}_anat.nii.gz"),
         image.resolve("${name}_mask.nii.gz")]
    }
    MOUSE_ALIGNANATMASK(Channel.fromList(subjects), register, validator)
    MOUSE_ALIGNANATMASK.out.mask.view { meta, mask -> "MASK ${meta.id} ${mask}" }
}
