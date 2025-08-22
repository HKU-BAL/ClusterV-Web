from flask import render_template, flash, redirect, url_for, session, request, make_response, jsonify, send_file, abort
from app import app
from app.forms import Upload_data, Upload_setting
import uuid
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import User, Task, Notification
from app.shared.utils import subprocess_popen, _run_command
import json


import sys

@app.before_request
def make_session_permanent():
    session.permanent = True


def _initial_user_pid(p_id):
    if User.query.filter_by(s_id=p_id).first() is None:
        # add new users
        u = User(s_id=p_id)
        db.session.add(u)
        db.session.commit()
        print("pid none")
        return


current_u = None
def get_current_user(p_id):
    global current_u
    # if current_u == None:
    current_u = User.query.filter_by(s_id=p_id).first()
    return current_u

check_init = None
def set_check_init():
    global check_init
    if check_init == None:

        # initial pid
        if session.get('user_info') is None:
            session['user_info'] = {}
        if 'user_g_id' not in session.get('user_info'):
            new_id = str(uuid.uuid4())
            session['user_info'] = {}
            session['user_info']['user_g_id'] = new_id

        # store in db
        p_id = session['user_info']['user_g_id']
        print(p_id)
        _initial_user_pid(p_id)

        app.config['DATA_INPUT_DIR'] = "%s/%s/%s/" % (app.config['OUTPUT_PATH'], p_id, "input")
        app.config['DATA_OUTPUT_DIR'] = "%s/%s/%s/" % (app.config['OUTPUT_PATH'], p_id, "output")

        os.makedirs(app.config['DATA_INPUT_DIR'], exist_ok=True)
        os.makedirs(app.config['DATA_OUTPUT_DIR'], exist_ok=True)

        app.config['STATIC_OUTPUT_DIR'] = "%s/%s/" % (app.config['BASE_STATIC'], p_id)
        os.makedirs(app.config['STATIC_OUTPUT_DIR'], exist_ok=True)

        #check_init = True
        print(p_id)
    return

@app.route('/ClusterVW/')
@app.route('/ClusterVW/index')
def index():
    set_check_init()

    # x = "{} {}".format(sys.version, sys.path)
    # flash('{} {}'.format(session['user_info'], x))
    # flash('{}'.format(app.config['DATA_INPUT_DIR']))
    return render_template('index.html', title='ClusterV-Web')


@app.route('/ClusterVW//upload_files', methods=['POST'])
def upload_files():
    set_check_init()
    # flash('{}'.format(session['user_info']))
    listOfBAM = os.listdir(app.config['DATA_INPUT_DIR'])  
    listOfBAM = [i for i in listOfBAM if i[-4:]=='.bam']
    if len(listOfBAM) >= app.config['MAX_BAM_ALLOW']:
        abort(400)

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        _path = app.config['DATA_INPUT_DIR']
        uploaded_file.save(_path + filename)
    return '', 204


@app.route('/ClusterVW/results', methods=['GET', 'POST'])
def results():
    set_check_init()
    # flash('{}'.format(session['user_info']))

    listOfBAM = os.listdir(app.config['DATA_OUTPUT_DIR'])  
    listOfBAM = [i+".bam" for i in listOfBAM if i[:2]=="cv"]

    p_id = session['user_info']['user_g_id']
    current_u = get_current_user(p_id)
    all_report = []
    is_have_report = False
    print("check results", listOfBAM)
    for _idx, _bam_f in enumerate(listOfBAM):
        _sample_id=_bam_f.split('.')[0]
        _current_out_dir = "{}/{}/".format(app.config['DATA_OUTPUT_DIR'], _sample_id)

        # read config
        _all_config = {}
        _config_f = "{}/{}/config.json".format(app.config['DATA_OUTPUT_DIR'], _sample_id)
        try:
            if os.path.exists(_config_f):
                with open(_config_f, "r") as F:
                    _all_config = json.load(F) 
        except:
            pass
        print(_all_config)

        # get table
        _sybtype_tsv = "{}/consensus/all_info.tsv".format(_current_out_dir)
        _subtype_report = {}
        if os.path.exists(_sybtype_tsv):
            is_have_report = True

            _subtype_tsv_header, _subtype_tsv_data = [], []
            _new_header = ["sample_id", "quasispecies_id", "abundance", "quasispecies_coverage", "snp_counts", "indel_counts", "median_AF"]
            with open(_sybtype_tsv, 'r') as F:
                _idx = 0
                for line in F:
                    row = line.strip().split()
                    
                    if _idx == 0:
                        # _subtype_tsv_header = row
                        _subtype_tsv_header = _new_header
                    else:
                        # print(row)
                        _r_sample_id = row[4]
                        _r_sample_idx = row[0].split("_")[-1]
                        _r_abundance = row[7]
                        _r_abundance = "%.4f" % (float(_r_abundance))
                        _tmp_row = row[-1].split(";")
                        _r_coverage = _tmp_row[0]
                        _r_snp_n = _tmp_row[1]
                        _r_indel_n = _tmp_row[2]
                        _r_median_af = _tmp_row[3]
                        _r_median_af = "%.4f" % (float(_r_median_af))

                        new_row = [_r_sample_id, _r_sample_idx, _r_abundance, _r_coverage, _r_snp_n, _r_indel_n, _r_median_af]

                        _subtype_tsv_data.append(new_row)
                    _idx += 1
            _subtype_report = {"header": _subtype_tsv_header, "data": _subtype_tsv_data}
        else:
            continue
        # get table
        _mutation_tsv = "{}/consensus/all_report.tsv".format(_current_out_dir)
        _mutation_report = {}
        if os.path.exists(_mutation_tsv):
            _mutation_tsv_header, _mutation_tsv_data = [], []
            _mutation_tsv_header = ["quasispecies", "quasispecies abundance", "gene", "mutation", "mutation type", "mutation score", "VAF in subtype", "drug class", "drug name", "drug score", "resistance level"]
            with open(_mutation_tsv, 'r') as F:
                _idx = 0
                for line in F:
                    row = line.strip().split("\t")
                    # if row[1] == "NA":
                    #     continue
                    if _idx == 0:
                        _mutation_tsv_header = _mutation_tsv_header
                    else:

                        _drug_class = row[2]
                        _drug_name = row[3]
                        _drug_score = row[4]
                        _d_level = row[5]
                        _g = row[1]
                        _m = row[12]
                        _mt = row[14]
                        _ms = row[13]
                        _s = row[7].split('_')[-1]
                        _sa = row[8]
                        _sa = "%.4f" % (float(_sa))
                        _v = row[10].split("|")[0]
                        _v = "%.4f" % (float(_v))
                        new_row = [_s, _sa, _g, _m, _mt, _ms, _v, _drug_class, _drug_name, _drug_score, _d_level, ]
                        # print(row)

                        _mutation_tsv_data.append(new_row)
                    _idx += 1

            _mutation_report = {"header": _mutation_tsv_header, "data": _mutation_tsv_data}

        lst_of_report = os.listdir("{}/{}".format(_current_out_dir, "consensus")) 
        lst_of_report = [i for i in lst_of_report if i[-4:]=='.png']

        get_d_report = {}
        _t_type = ['abundance_report', 'subtype_report', 'mutation_report']
        _t_name = ["{}_clustering_rst.png".format(_sample_id), "all_mutation_and_drug_ressitant_barplot.png", "all_mutation_and_drug_ressitant_heatmap.png"]
        for _i, _k in zip(_t_type, _t_name):
            if _k in lst_of_report:
                get_d_report[_i] = "{}/{}/{}".format(p_id, _sample_id, _k)

        all_report.append({"id": _sample_id, "png": get_d_report, "table_subtype": _subtype_report, "mutation_report":_mutation_report, "all_config": _all_config})
        # print(all_report)


    task_in_progression = []
    for _task in current_u.get_tasks_in_progress():
        task_in_progression.append({"task": _task.description, "progress": _task.get_progress()})
    print("find task in progress {}".format(task_in_progression))
    if request.method == 'POST':
        if request.form['action'] == 'Stop all tasks':
            if current_u.get_tasks_in_progress():
                current_u.stop_all_tasks()
        elif request.form['action'] == 'Delete all tasks':
            if current_u.get_tasks_in_progress():
                flash('{}'.format('delete all'))
                current_u.stop_all_tasks()
                current_u.delete_all_task()
                db.session.commit()
                return redirect(url_for('upload_data'))
        elif request.form['action'] == 'Check running stage':
            pass
        else:
            pass

    return render_template('results.html', title='results', task_in_progression=task_in_progression, current_u=current_u, all_report=all_report, is_have_report=is_have_report)
    
    

@app.route('/ClusterVW//analysis', methods=['GET', 'POST'])
def analysis():
    set_check_init()

    listOfBAM = os.listdir(app.config['DATA_INPUT_DIR'])  
    listOfBAM = [i for i in listOfBAM if i[:2]=="cv" and i[-4:]=='.bam']

    form = Upload_setting()
    if request.method == 'POST':
        p_id = session['user_info']['user_g_id']
        current_u = get_current_user(p_id)
        flash('run_task, {}'.format(current_u.id))

        for _idx, _bam_f in enumerate(listOfBAM):
            _sample_id=_bam_f.split('.')[0]
            _current_out_dir = "{}/{}/".format(app.config['DATA_OUTPUT_DIR'], _sample_id)
            _current_static_out_dir = "{}/{}/".format(app.config['STATIC_OUTPUT_DIR'], _sample_id)

            current_u.launch_task("run_clusterv", _sample_id, _sample_id, _bam_f, app.config['DATA_INPUT_DIR'], _current_out_dir, _current_static_out_dir)
            db.session.commit()
            db.session.refresh(current_u)

        return redirect(url_for('results'))

    return render_template('analysis.html', title='configuration', form=form, listOfBAM=listOfBAM)



def run_clusterv_task(_config):
    all_f = os.listdir(app.config['DATA_INPUT_DIR'])  
    listOfBAM = [i for i in all_f if i[:2]=="cv" and  i[-4:]=='.bam']

    p_id = session['user_info']['user_g_id']
    current_u = get_current_user(p_id)

    print('run_task, pid {}'.format(current_u.id))
    for _idx, _bam_f in enumerate(listOfBAM):
        _sample_id=_bam_f.split('.')[0]
        _current_out_dir = "{}/{}/".format(app.config['DATA_OUTPUT_DIR'], _sample_id)
        _current_static_out_dir = "{}/{}/".format(app.config['STATIC_OUTPUT_DIR'], _sample_id)

        cmd = "mkdir -p {}; cp {}/config.json {}".format(_current_out_dir, app.config['DATA_INPUT_DIR'], _current_out_dir)
        _run_command(cmd)

        current_u.launch_task("run_clusterv", _sample_id, _sample_id, _bam_f, app.config['DATA_INPUT_DIR'], _current_out_dir, _current_static_out_dir, app.config['CV_PATH'], _config)
        db.session.commit()
        db.session.refresh(current_u)
    return 0

def allowed_file_ext(filename, ext):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ext


@app.route('/ClusterVW//upload_data', methods=['GET', 'POST'])
def upload_data():
    set_check_init()

    all_f = os.listdir(app.config['DATA_INPUT_DIR'])  
    listOfBAM = [i for i in all_f if i[-4:]=='.bam']
    listOfjson = [i for i in all_f if i[-4:]=='.json']

    _file_ref = [i for i in all_f if i[-3:]=='.fa' or i[-3:]=='sta']
    _file_ref = None if len(_file_ref) < 1 else _file_ref[0]
    _file_bed = [i for i in all_f if i[-3:]=='bed']
    _file_bed = None if len(_file_bed) < 1 else _file_bed[0]

    # read config
    all_config = {}
    _config_f = "{}/config.json".format(app.config['DATA_INPUT_DIR'])
    try:
        _config_f = "{}/{}".format(app.config['DATA_INPUT_DIR'], listOfjson[0])
    except:
        pass
    if os.path.exists(_config_f):
        with open(_config_f, "r") as F:
            all_config = json.load(F) 

        if _file_ref != None:
            with open("{}/{}.fai".format(app.config['DATA_INPUT_DIR'], _file_ref), "r") as F:
                row = F.readline().strip().split("\t")
                all_config["ref_contig"] = row[0]
                all_config["ref_len"] = row[1]

        if _file_bed != None:
            with open("{}/{}".format(app.config['DATA_INPUT_DIR'], _file_bed), "r") as F:
                row = F.readline().strip().split("\t")
                all_config["bed_contig"] = row[0]
                all_config["bed_l"] = row[1]
                all_config["bed_r"] = row[2]
    # print(all_config)


    #print(_file_ref, _file_bed)
    if request.method == 'POST':
        if request.form['submit'] == 'Apply Configuration':
            # upload ref
            try:
                file = request.files['input_fasta_f']
                if file and allowed_file_ext(file.filename, ["fa", "fasta"]):
                    filename = secure_filename(file.filename)

                    # overwrite original one
                    cmd = "rm -rf {}/*.fa {}/*.fasta {}/*.fai".format(app.config['DATA_INPUT_DIR'], app.config['DATA_INPUT_DIR'], app.config['DATA_INPUT_DIR'])
                    _run_command(cmd)
                    
                    file.save(os.path.join(app.config['DATA_INPUT_DIR'], filename))
                    cmd = "samtools faidx {}".format(app.config['DATA_INPUT_DIR']+filename)
                    _run_command(cmd)
                    flash('using ref file: {}'.format(filename))
                    _file_ref = filename
            except Exception as e:
                pass

            # upload bed
            try:
                file = request.files['input_bed_f']
                if file and allowed_file_ext(file.filename, ["bed"]):
                    filename = secure_filename(file.filename)
                    
                    # overwrite original one
                    cmd = "rm -rf {}/*.bed".format(app.config['DATA_INPUT_DIR'])
                    _run_command(cmd)

                    file.save(os.path.join(app.config['DATA_INPUT_DIR'], filename))
                    _file_bed = filename
                    flash('using BED file: {}'.format(filename))
            except Exception as e:
                pass

            # handle Ref file
            if _file_ref == None:
                # copy reference file
                _file_ref = "HIV_1.fasta"
                cmd = "cp {} {} ; samtools faidx {}".format(app.config['BASE_REF_PATH'], app.config['DATA_INPUT_DIR'], app.config['DATA_INPUT_DIR']+"/HIV_1.fasta")
                _run_command(cmd)

            # handle BED file
            if _file_bed == None:
                _bed_f_path = "{}/HIV_1_region.bed".format(app.config['DATA_INPUT_DIR'])
                _file_bed = "HIV_1_region.bed"
                # read contig
                _ref_index_path = "{}/{}.fai".format(app.config['DATA_INPUT_DIR'], _file_ref)
                with open(_ref_index_path, 'r') as F:
                    for line in F:
                        row = line.strip().split()
                        _contig, _l_pos, _r_pos = row[0], 1, int(row[1]) - 1
                        break
                with open(_bed_f_path, "w+") as F:
                    F.write("{}\t{}\t{}\n".format(_contig, _l_pos, _r_pos-1))
                flash('using BED region: {} {}-{}'.format(_contig, _l_pos, _r_pos))

            # check parameters
            try:
                indel_l = int(request.form.get('indel_l'))
                top_k = int(request.form.get('top_k'))
                n_min_supports = int(request.form.get('n_min_supports'))
                hivdb_url = request.form.get('hivdb_url')

                min_af = float(request.form.get('min_af'))
                n_max_coverage = int(request.form.get('n_max_coverage'))
                n_of_read_for_consensus = request.form.get('n_of_read_for_consensus')
                flye_nano_type = request.form.get('flye_nano_type')
                flye_genome_size = request.form.get('flye_genome_size')

                if indel_l < 0:
                    flash('Error: requires indel_l >= 0')
                    return redirect(url_for('upload_data')+'#g_info')

                if top_k < 2:
                    flash('Error: requires top_k >= 2')
                    return redirect(url_for('upload_data')+'#g_info')

                if n_min_supports < 1:
                    flash('Error: requires n_min_supports >= 1')
                    return redirect(url_for('upload_data')+'#g_info')

                if hivdb_url != "" and "sierra" not in hivdb_url:
                    flash('Error: hivdb_url {} invalid'.format(hivdb_url))
                    return redirect(url_for('upload_data')+'#g_info')

                if min_af < 0 or min_af > 1:
                    flash('Error: requires min_af in (0, 1)')
                    return redirect(url_for('upload_data')+'#g_info')

                if n_max_coverage > 50000:
                    flash('Error: requires n_max_coverage > 50000')
                    return redirect(url_for('upload_data')+'#g_info')

                _config = {
                "indel_l": indel_l,
                "top_k": top_k,
                "n_min_supports": n_min_supports,
                "flye_genome_size": flye_genome_size,
                "hivdb_url": hivdb_url,
                "file_ref": _file_ref,
                "file_bed": _file_bed,
                "min_af": min_af,
                "n_max_coverage": n_max_coverage,
                "n_of_read_for_consensus": n_of_read_for_consensus,
                "flye_nano_type": flye_nano_type
                }
                jo = json.dumps(_config, indent=4)

                all_f = os.listdir(app.config['DATA_INPUT_DIR'])  
                listOfjson = [i for i in all_f if i[-4:]=='json']
                print(listOfjson)
                _json_i = 0
                try:
                    _json_i = int(len([i for i in listOfjson if "_" in i]))
                except:
                    pass
                _json_i += 1
                with open("{}/{}_config.json".format(app.config['DATA_INPUT_DIR'], _json_i), "w") as F:
                    F.write(jo)
                with open("{}/config.json".format(app.config['DATA_INPUT_DIR']), "w") as F:
                    F.write(jo)
            except:
                flash('Error: Configuration invalid, please check file type accordingly')
                return redirect(url_for('upload_data')+'#g_info')
            

            all_f = os.listdir(app.config['DATA_INPUT_DIR'])  
            listOfjson = [i for i in all_f if i[-4:]=='json']
            print(listOfjson)
            _json_i = 0
            try:
                _json_i = int(len([i for i in listOfjson if "_" in i]))
            except:
                pass

            listOfBAM = [i for i in all_f if i[:2] != "cv" and i[-4:]=='.bam']
            #n_cv = len([i for i in all_f if i[:2] == "cv" and i[-4:]=='.bam'])
            print(_json_i)
            n_cv = _json_i
            for _idx, _bam in enumerate(listOfBAM):
                print(_bam)
                if _bam[:2] == "cv":
                    _bam = "_".join(_bam.split("_")[1:])
                cmd = "cp {}/{} {}/cv{}_{}".format(app.config['DATA_INPUT_DIR'], _bam, app.config['DATA_INPUT_DIR'], n_cv+_idx, _bam)
                _run_command(cmd)
            return redirect(url_for('upload_data')+'#3_run')
        elif request.form['submit'] == 'Run analysis':
            if all_config == {}:
                flash('Error: no configuration found, please set the "Apply Configuration')
                return redirect(url_for('upload_data')+'#g_info')

            if all_config["bed_contig"] != all_config["ref_contig"]:
                flash('Error: config name in fasta and BED are different, please reupload reference or BED file.')
                return redirect(url_for('upload_data')+'#g_info')

            # check if input is valid
            if len(listOfBAM) < 1:
                flash('no BAM file uploaded, please upload your BAMs before runing analysis')
                redirect(url_for('upload_data'))

            # run clusterv task
            run_clusterv_task(all_config)
            return redirect(url_for('results'))
        elif request.form['submit'] == 'Upload data':
            return redirect(url_for('upload_data')+'#2_config')

   
    n_listOfBAM = [i for i in listOfBAM if i[:2]=="cv" and i[-4:]=='.bam']
    print(n_listOfBAM)
    if len(n_listOfBAM) != 0:
        listOfBAM = n_listOfBAM
    else:
        all_config = None

    return render_template('update_data.html', title='Upload data', listOfBAM=listOfBAM, file_ref=_file_ref, file_bed=_file_bed, all_config=all_config)

@app.route('/ClusterVW//download_all_results')
def download_all_results():
    set_check_init()

    listOfBAM = os.listdir(app.config['DATA_OUTPUT_DIR'])  
    listOfBAM = [i+".bam" for i in listOfBAM if i[:2]=="cv"]
    flies_lst = []
    for _idx, _bam_f in enumerate(listOfBAM):
        _sample_id=_bam_f.split('.')[0]
        _current_out_dir = "{}/{}/consensus".format(app.config['DATA_OUTPUT_DIR'], _sample_id)
        _sybtype_tsv = "{}/all_info.tsv".format(_current_out_dir)
        if os.path.exists(_sybtype_tsv):
            flies_lst.append("{}/consensus/*.tsv {}/consensus/*.json {}/consensus/*.png {}/consensus/*.fasta".format(_sample_id, _sample_id, _sample_id, _sample_id))
            flies_lst.append("{}/consensus/*/*bam* {}/consensus/*/*_cs.vcf {}/consensus/*/*low_af.vcf*".format(_sample_id, _sample_id, _sample_id))

    tar_f = "{}/{}.zip".format(app.config['DATA_OUTPUT_DIR'], "clusterv_results")
    cmd = 'cd {}; rm -rf {}; zip -r {} {}'.format(app.config['DATA_OUTPUT_DIR'], tar_f, tar_f, " ".join(flies_lst))
    _run_command(cmd)
    return send_file(tar_f, as_attachment=True)

@app.route('/ClusterVW//download_example_bed')
def download_example_bed():
    set_check_init()
    tar_f = "{}/HIV_1_amplicon_region.bed".format(app.config['APP_DATA_PATH'])
    return send_file(tar_f, as_attachment=True)


@app.route('/ClusterVW//download_example_data')
def download_example_data():
    set_check_init()
    tar_f = "{}/clusterv_example.zip".format(app.config['APP_DATA_PATH'])
    return send_file(tar_f, as_attachment=True)



@app.route('/ClusterVW//delete_all_results')
def delete_all_results():
    set_check_init()
    try:
        _output_dir = app.config['DATA_OUTPUT_DIR']
        cmd = "rm -rf {}/*".format(_output_dir)
        _run_command(cmd)
        return redirect(url_for('results'))
    except Exception as e:
        return f"Error in deleting files: {e}"
    redirect(url_for('results'))



@app.route('/ClusterVW//remove_bam')
def remove_bam():
    set_check_init()

    try:
        _input_dir = app.config['DATA_INPUT_DIR']
        cmd = "rm -rf {}/*.bam*".format(_input_dir)
        _run_command(cmd)
        return redirect(url_for('upload_data'))
    except Exception as e:
        return f"Error in deleting files: {e}"

@app.route('/ClusterVW//status', methods=['GET'])
def getStatus():

    set_check_init()

    listOfBAM = os.listdir(app.config['DATA_INPUT_DIR'])  
    listOfBAM = [i for i in listOfBAM if i[:2]=="cv" and i[-4:]=='.bam']

    p_id = session['user_info']['user_g_id']
    current_u = get_current_user(p_id)

    # print("status {}".format(p_id))
    # print("status u {}".format(current_u))
    statusList = {}
    for _task in current_u.get_tasks_in_progress():
        if _task.user_id == current_u.id:
            print(_task, current_u)
            statusList[_task.description] = _task.get_progress()
    # print(statusList)
    return json.dumps(statusList)

