process MOUSE_BET {
    label 'process_high'

    container "scilus/scilpy:dev"

    input:
        tuple val(meta), path(anat)
    output:
        tuple val(meta), path("*__mask.nii.gz")      , emit: mask
        path "versions.yml"                          , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"

    """

    brain_extraction.py $anat ${prefix}__mask.nii.gz
    fslmaths ${prefix}__mask.nii.gz -bin ${prefix}__mask.nii.gz
    scil_volume_math convert ${prefix}__mask.nii.gz ${prefix}__mask.nii.gz -f --data_type int8

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        scilpy: \$(uv pip -q -n list | grep scilpy | tr -s ' ' | cut -d' ' -f2)
    END_VERSIONS
    """

    stub:
    """
    fslmaths
    scil_volume_math -h

    touch all__stats.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        scilpy: \$(uv pip -q -n list | grep scilpy | tr -s ' ' | cut -d' ' -f2)
    END_VERSIONS
    """
}