process MOUSE_VALIDATEINVIVOMASK {
    tag "$meta.id"
    label 'process_low'
    container "scilus/scilus:2.2.2"
    conda "${moduleDir}/environment.yml"

    input:
        tuple val(meta), path(b0), path(mask)
        path validator

    output:
        tuple val(meta), path(mask), emit: mask

    script:
    """
    python '$validator' '$b0' '$mask' --require-match
    """

    stub:
    """
    echo 'Skipping mask validation in stub run'
    """
}
