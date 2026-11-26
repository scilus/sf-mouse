process MOUSE_CONVERTBET {
    tag "$meta.id"
    label 'process_low'
 
    container "scilus/scilus:2.2.0"

    input:
        tuple val(meta), path(image)
    output:
        tuple val(meta), path("*_mask.nii.gz")                      , emit: mask
        path "versions.yml"                                         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def nb_vox = task.ext.nb_vox ?: ""
    """
    fslmaths ${image} -bin ${prefix}_mask.nii.gz

    scil_volume_math erosion ${prefix}_mask.nii.gz $nb_vox ${prefix}_mask.nii.gz --data_type uint8 -f
    ImageMath 3 ${prefix}_mask.nii.gz  GetLargestComponent ${prefix}_mask.nii.gz 
    scil_volume_math dilation ${prefix}_mask.nii.gz $nb_vox ${prefix}_mask.nii.gz --data_type uint8 -f
    ImageMath 3 ${prefix}_mask.nii.gz  FillHoles ${prefix}_mask.nii.gz 

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
	    scilpy: \$(uv -q -n pip list | grep scilpy | tr -s ' ' | cut -d' ' -f2)
        fsl: \$(flirt -version 2>&1 | sed -n 's/FLIRT version \\([0-9.]\\+\\)/\\1/p')
        ants: \$(ImageMath --version 2>&1 | sed -n 's/ANTs Version: v\\([0-9.]\\+\\)/\\1/p')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}_mask.nii.gz 

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        scilpy: \$(uv pip -q -n list | grep scilpy | tr -s ' ' | cut -d' ' -f2)
        fsl: \$(flirt -version 2>&1 | sed -n 's/FLIRT version \\([0-9.]\\+\\)/\\1/p')
        ants: \$(ImageMath --version 2>&1 | sed -n 's/ANTs Version: v\\([0-9.]\\+\\)/\\1/p')
    END_VERSIONS
    """
}