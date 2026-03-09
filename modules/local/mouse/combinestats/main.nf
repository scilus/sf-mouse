process MOUSE_COMBINESTATS {
    label 'process_high'

    container "scilus/scilpy:dev"

    input:
        path(stats_list)
    output:
        path "all_stats.json"   , emit: stats_json
        path "all_stats.xlsx"   , emit: stats_xlsx
        path "versions.yml"      , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def convert_to_xlsx = task.ext.convert_to_xlsx ?: false
    
    if ( task.ext.key ) args += " --extra_key nb-vx-seed"
    """
    shopt -s extglob
    mkdir stats
    
    for curr_stat in $stats_list;
    do
        bname=\${curr_stat/stats/}
        mv \$curr_stat stats/\${bname}
    done

    scil_json_merge_entries stats/*json all_stats.json --keep_separate

    if $convert_to_xlsx; then
        scil_json_convert_entries_to_xlsx all_stats.json all_stats.xlsx $args
    fi

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        scilpy: \$(uv pip -q -n list | grep scilpy | tr -s ' ' | cut -d' ' -f2)
    END_VERSIONS
    """

    stub:
    """
    scil_json_merge_entries -h
    scil_json_convert_entries_to_xlsx -h

    touch all__stats.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        scilpy: \$(uv pip -q -n list | grep scilpy | tr -s ' ' | cut -d' ' -f2)
    END_VERSIONS
    """
}