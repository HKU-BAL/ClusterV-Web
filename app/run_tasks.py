import time
from rq import get_current_job
from app import app
from app import db
from app.models import User, Task
from app.shared.utils import subprocess_popen, _run_command

app.app_context().push()

def run_example(seconds):
    job = get_current_job()

    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()

        print(i)

        time.sleep(1)
    job.meta['progress'] = "ASDASD"
    job.save_meta()
    print('Task completed')


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        task.s_progress=progress
        print(progress)
        if str(progress) == "100":
            task.complete = True
        db.session.commit()



def example(pid, seconds):
    job = get_current_job()
    _set_task_progress(0)

    print('Starting task')
    for i in range(seconds):
        # job.meta['progress'] = 100.0 * i / seconds
        # job.save_meta()

        print(i)
        _set_task_progress(100.0 * i / seconds)

        time.sleep(1)
    # job.meta['progress'] = "ASDASD"
    # job.save_meta()
    _set_task_progress(100)
    print('Task completed')

def run_clusterv(pid, sample_id, bam_fn, input_dir, output_dir, current_static_out_dir, CV_path, _config):

    print(">>>>>>>>>>>>> {}, {}".format(bam_fn, _config))
    job = get_current_job()

    # print(job)
    _set_task_progress(0)

    _ref_f = "{}/{}".format(input_dir, _config['file_ref'])
    _bed_f = "{}/{}".format(input_dir, _config['file_bed'])
    _run_threads = "8"


    ## creating bam index
    #cmd = 'cp {}/config.json {}'.format(input_dir, output_dir)
    #try:
    #    _run_command(cmd)
    #except:
    #    _set_task_progress("error copy config files")

    # creating bam index
    cmd = 'samtools index %s' % (input_dir+bam_fn)
    try:
        _run_command(cmd)
        _set_task_progress(10)
    except:
        _set_task_progress("error in indexing bam file, please make sure you upload a valid bam file")
        return


    # check bam coverage
    cmd = 'mkdir -p {}/check_cov && mosdepth {}/check_cov/ori {} -b {}'.format(output_dir, output_dir, input_dir+bam_fn, _bed_f)
    try:
        _run_command(cmd)
        _set_task_progress(20)
    except:
        _set_task_progress("error in check_bam coverage")
        return

    # run initial task
    print('Starting run clusterV')
    COMMON_OPT="--clair_ensemble_threads {} --ref_fn {} --bed_fn {}".format(_run_threads, _ref_f, _bed_f)
    
    cmd = "python {} run_initial_call {} --bam_fn {} --sample_id {} --out_dir {} --indel_l {}".format(CV_path, 
                COMMON_OPT, input_dir+bam_fn, sample_id, output_dir, _config['indel_l'])

    try:
        _run_command(cmd)
        _set_task_progress(30)
    except:
        _set_task_progress("error in run initial clusterv call")
        return

    # check filtered coverage
    cmd = 'mosdepth {}/check_cov/new {}/{}_f.bam -b {}'.format(output_dir, output_dir, sample_id, _bed_f)
    _run_command(cmd)
    # _set_task_progress(30)
    try:
        _run_command(cmd)
        _set_task_progress(35)
    except:
        _set_task_progress("error, no read after clusterv filtering")
        return
    


    _min_af = _config['min_af']
    _n_max_coverage = _config['n_max_coverage']

    _top_k = _config['top_k']
    _n_min_supports = _config['n_min_supports']

    _clair_ensemble_threads = "8"
    _subtype_parallel = "2"

    # run clustering
    cmd = "python {} run_ClusterV {} --bam {}_f.bam --vcf {}.v/out.vcf --out_dir {}/clustering --sample_id {} --min_af {} --n_min_supports {} --top_k {} --clair_ensemble_threads {} --subtype_parallel {} --n_max_coverage {} > {}/run_clustering.log".format(
            CV_path, COMMON_OPT, output_dir+sample_id, output_dir+sample_id, output_dir, sample_id, _min_af, _n_min_supports, _top_k,
            _clair_ensemble_threads, _subtype_parallel, _n_max_coverage, output_dir)

    try:
        _run_command(cmd)
        _set_task_progress(80)
    except:
        _set_task_progress("error in run clusterv")
        return


    COMMON_OPT="--threads {} --ref_fn {} --bed_fn {}".format(_run_threads, _ref_f, _bed_f)
    _hivdb_url = _config['hivdb_url']

    _n_of_read_for_consensus = _config['n_of_read_for_consensus']
    _flye_genome_size = _config['flye_genome_size']
    _flye_nano_type = _config['flye_nano_type']

    if len(_hivdb_url) > 1:
        COMMON_OPT += " --hivdb_url {}".format(_hivdb_url)

    cmd = "python {} get_consensus {} --out_dir {}/consensus --flye_genome_size {} --flye_nano_type {} --n_of_read_for_consensus {} --tar_tsv {}/clustering/all_clusters_info.tsv > {}/get_consensus.log".format(
            CV_path, COMMON_OPT, output_dir, _flye_genome_size, _flye_nano_type, _n_of_read_for_consensus, output_dir, output_dir)
    
    try:
        _run_command(cmd)
        _set_task_progress(100)
    except:
        _set_task_progress("error in run get consensus, no consensus found")
        return
    print('Task completed')

    cmd = 'mkdir -p {}; cp {}/consensus/*.png {}'.format(current_static_out_dir, output_dir, current_static_out_dir)
    _run_command(cmd)

    ori_lst = []
    with open("{}/consensus/all_info.tsv".format(output_dir), "r") as F:
        for line in F:
            row = line.strip().split("\t")
            if "output" in row[1]:
                row[1] = "".join(row[1].split("output")[1])
                row[2] = "".join(row[2].split("output")[1])
                row[3] = "".join(row[3].split("output")[1])
            ori_lst.append(row)

    cmd = 'cp {}/consensus/all_info.tsv {}/consensus/all_info.tsv_bak'.format(output_dir, output_dir)
    _run_command(cmd)
    with open("{}/consensus/all_info.tsv".format(output_dir), "w") as F:
        for row in ori_lst:
            F.write("%s\n" % ("\t".join(row)))

    # # clean files
    # cmd = 'rm -rf {}*.bam* {}.v/ {}/clustering {}/consensus/info.tsv'.format(output_dir+sample_id, output_dir+sample_id, output_dir, output_dir)
    # _run_command(cmd)

