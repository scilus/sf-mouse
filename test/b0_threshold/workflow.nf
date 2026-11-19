include { IMAGE_POWDERAVERAGE } from '../../modules/nf-neuro/image/powderaverage/main.nf'
include { MOUSE_REGISTRATION } from '../../modules/local/mouse/register/main.nf'
include { RECONST_FRF } from '../../modules/nf-neuro/reconst/frf/main.nf'
include { RECONST_QBALL } from '../../modules/nf-neuro/reconst/qball/main.nf'

workflow NNUNET {
    take:
    images
    main:
    IMAGE_POWDERAVERAGE(images)
}

workflow {
    meta = [id: 'subject']
    dwi = file(params.dwi)
    bval = file(params.bval)
    bvec = file(params.bvec)
    mask = file(params.mask)
    if (params.component == 'powder') {
        NNUNET(Channel.of([meta, dwi, bval, []]))
    }
    else if (params.component == 'registration') {
        MOUSE_REGISTRATION(Channel.of([meta, dwi, bval, bvec, mask]))
    }
    else if (params.component == 'frf') {
        RECONST_FRF(Channel.of([meta, dwi, bval, bvec, mask, [], [], []]))
    }
    else if (params.component == 'qball') {
        RECONST_QBALL(Channel.of([meta, dwi, bval, bvec, mask]))
    }
    else {
        error "Unknown component: ${params.component}"
    }
}
