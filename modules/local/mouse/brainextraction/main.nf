process MOUSE_BRAINEXTRACTION {
    tag "$meta.id"
    label 'process_high'

    container "scilus/antspynet:dev"

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
    antsMouseBrainExtraction $anat ${prefix}__mask.nii.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ants: \$(antsMouseBrainExtraction --version 2>&1 | sed -n 's/ANTs Version: v\\([0-9.]\\+\\)/\\1/p')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    antsMouseBrainExtraction -h

    touch ${prefix}__mask.nii.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ants: \$(antsMouseBrainExtraction --version 2>&1 | sed -n 's/ANTs Version: v\\([0-9.]\\+\\)/\\1/p')
    END_VERSIONS
    """
}