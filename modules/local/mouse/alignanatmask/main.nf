def parse_invivo_register_anat(value) {
    if (value instanceof Boolean) return value
    if (value instanceof String && value.toLowerCase() in ['true', 'false']) return value.toBoolean()
    throw new IllegalArgumentException("invivo_register_anat must be true or false, got '${value}'")
}

process MOUSE_ALIGNANATMASK {
    tag "$meta.id"
    label 'process_high'
    container "scilus/scilus:2.2.2"
    conda "${moduleDir}/environment.yml"

    input:
        tuple val(meta), path(b0, name: 'reference_b0.nii.gz'), path(anat, name: 'anat.nii.gz'), path(mask, name: 'anat_mask.nii.gz')
        val register_anat
        path validator

    output:
        tuple val(meta), path("*__anat_dwi_mask.nii.gz"), emit: mask
        path "versions.yml", emit: versions

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def align = register_anat ? """
    antsRegistrationSyNQuick.sh -d 3 -f '$b0' -m '$anat' -t r -o ${prefix}__anat_to_dwi_ -n ${task.cpus}
    antsApplyTransforms -d 3 -i '$mask' -r '$b0' -t ${prefix}__anat_to_dwi_0GenericAffine.mat -n NearestNeighbor -o ${prefix}__anat_dwi_mask.nii.gz
    """ : """
    if [ "\$grid" = "same" ]; then
        cp '$mask' ${prefix}__anat_dwi_mask.nii.gz
    else
        echo 'Resampling anatomical mask without registration; verify anatomical alignment.' >&2
        antsApplyTransforms -d 3 -i '$mask' -r '$b0' -t identity -n NearestNeighbor -o ${prefix}__anat_dwi_mask.nii.gz
    fi
    """
    """
    grid=\$(python '$validator' '$b0' '$mask' --anatomy '$anat')
    $align
    python '$validator' '$b0' ${prefix}__anat_dwi_mask.nii.gz --require-match
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ants: \$(antsRegistration --version | grep "Version" | sed -E 's/.*: v?([0-9.a-zA-Z-]+).*/\\1/')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}__anat_dwi_mask.nii.gz versions.yml
    """
}
