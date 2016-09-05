from jenkins import Jenkins


jk = Jenkins('http://192.168.40.218:8081/', 'gzliuxin', 'zzxx123')


def build_job(serialno, moa_script=""):
    params = {
        'serialno': serialno,
        # 'moa_script': moa_script,
    }
    jk.build_job('run_one_pipe', params, 'this.is.a.test.token')


if __name__ == '__main__':
    build_job('HT5BGBE03355')
    build_job('HC46FWY05694')
