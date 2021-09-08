#!/usr/bin/python3

import time
import http.client as hc
import urllib.parse
#import pandas as pd
from bs4 import BeautifulSoup
from clint.textui import progress
import moviepy.video as mv
import moviepy.editor as me
from multiprocessing import Process
import portalocker
import os
import sys
import tempfile
from shutil import copyfile
import ssl

  

#result_file = 'result.mkv'

basedir = os.path.abspath(os.path.dirname(__file__))

path = basedir+'/tmp/'

log_filename = path+'/mkv_log.txt'

form = '.ts'


def get_html_request(targetLink):
    ssl._create_default_https_context = ssl._create_unverified_context

    url = urllib.parse.urlparse(targetLink)

    headers = {'User-Agent': 'Mozilla/5.0'}
    

    con = hc.HTTPSConnection(url.netloc)
    #targetUrl = url.path+';'+url.params+'?'+url.query+'#'+url.fragment
    targetUrl = url.path
    if url.params:
        targetUrl += ';'+url.params
    if url.query:
        targetUrl += '?'+url.query
    if url.fragment:
        targetUrl += '#'+url.fragment

    con.request('GET', targetUrl, headers=headers)
    res = con.getresponse()
    #print(res, res.status, res.reason, res.headers)
    return res


def download_video(idx, epoch, targetLink):
    start = time.time()

    res = get_html_request(targetLink)
    body = res.read()
    if len(body) is 0:
        new_link = res.getheader("Location")
        #print(new_link)
        download_video(idx, epoch, new_link)
        return
    #print(body)

    #form = '.mp4'

    #file_name = str(epoch)+'_'+str(idx)+form
    file_name = str(idx)+form

    with portalocker.Lock(path+file_name, 'wb') as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())
        #print('saved', file_name)
    
    f.close()

    end = time.time()
    #print('Download video', file_name, 'time :', end-start)



def download_link_list(link_list, result_file="result.mkv"):

    start = time.time()

    processes = [[],[]]
    epoch = 0
    size = 50

    concat_processes = []

    #print(link_list)
    for idx, line in enumerate(progress.bar(link_list)):
            try:
                #if idx > 10:
                    #break
                process = Process(target=download_video, args=(idx, epoch, line))
                processes[(epoch+1)%2].append(process)
                process.start()
                #link_list.remove(line)
            except:
                pass
            if idx+1 >= (epoch+1)*size or idx+1 == len(link_list):
                #for process in progress.bar(processes):
                for process in processes[epoch%2]:
                    try:
                        process.join()
                    except:
                        pass
                processes[epoch%2] = []
                #sorted_list = sorted([fn for fn in os.listdir(path) if fn.endswith('.mp4') and not fn.startswith('res_') and int(fn.split('_')[0]) == epoch], key=lambda x: int(x.split('.')[0].split('_')[1]))
                #print(sorted_list)

                #process = Process(target=concatenate, args=(epoch, sorted_list))
                #concat_processes.append(process)
                #process.start()
                epoch+=1


    #for process in concat_processes:
    for process in processes:
        try:
            process.join()
        except:
            pass
    
             
    sorted_list = sorted([path+fn for fn in os.listdir(path) if fn.endswith(form) and not fn.startswith('res_')], key=lambda x: int(x.split('/')[-1].split('.')[0]))

    chunk = 500
    
    lsize = len(sorted_list)//chunk

    if os.path.isfile(log_filename):
        os.remove(log_filename)

    for chunk_id in range(lsize):
        os.system("mkvmerge -o "+path+"res_"+str(chunk_id)+".mkv '[' "+' '.join(sorted_list[chunk_id*chunk:(chunk_id+1)*chunk])+" ']'")
        #os.system("mkvmerge -o "+path+"res_"+str(chunk_id)+".mkv '[' "+' '.join(sorted_list[chunk_id*chunk:(chunk_id+1)*chunk])+" ']'"+" >> "+log_filename)
        #print("mkvmerge -o "+path+"res_"+str(chunk_id)+".mkv '[' "+' '.join(sorted_list[chunk_id*chunk:(chunk_id+1)*chunk])+" ']'")
    os.system("mkvmerge -o "+path+"res_"+str(lsize)+".mkv '[' "+' '.join(sorted_list[(lsize-1)*chunk:])+" ']'")
    #os.system("mkvmerge -o "+path+"res_"+str(lsize)+".mkv '[' "+' '.join(sorted_list[(lsize-1)*chunk:])+" ']'"+" >> "+log_filename)

    res_list = sorted([path+fn for fn in os.listdir(path) if fn.endswith('.mkv') and fn.startswith('res_')], key=lambda x: int(x.split('/')[-1].split('.')[0].split('_')[-1]))
    #print(res_list)

    os.system("mkvmerge -o "+result_file+" '[' "+' '.join(res_list)+" ']'")
    #os.system("mkvmerge -o "+result_file+" '[' "+' '.join(res_list)+" ']'"+" >> "+log_filename)
    #print("mkvmerge -o result.mkv '[' "+' '.join(res_list)+" ']'")

    for i in sorted_list:
        os.remove(i)
    for i in res_list:
        os.remove(i)



    end = time.time()
    print('Collect time :', end-start)



def download_m3u8(m3u8_link):
    res = get_html_request(m3u8_link)
    body = res.read()

    print(res.status, res.reason, res.msg)


    link_list = [i for i in body.decode('utf-8').split('\n') if not i.startswith('#') and len(i) > 0 and i.endswith(form)]

    download_link_list(link_list)
    



def collect_playlist_from_link(targetLink):

    page = get_html_request(targetLink)

    soup = BeautifulSoup(page.read())

    codes = soup.findAll('div', class_='translationCode')
    if len(codes) == 0:
        codes = soup.findAll('a', class_='buyTranslationApi')
    if len(codes) == 0:
        print('Видео не найдено')

    for element in codes:
        video_id = element['data-remote-translation-id']

        #m3u8_link = "https://bl.webcaster.pro/media/playlist/free_42f7925671a025920acfabe096cff0d2/21_1839438366/720p/a1a12514e205857ed28c780f84c6583d/"+video_id+".m3u8"
        m3u8_link = "https://bl.webcaster.pro/media/playlist/free_8f64246dedb1f953fd19369b977e3726/21_8960345018/720p/59d3135b82846cccc08c4318ef3a75cc/"+video_id+".m3u8"
        print('m3u8 link', m3u8_link)
        download_m3u8(m3u8_link)

    

def collect_playlist_from_file(file_name):
    f = open(file_name, 'r')
    link_list = [i.replace('\n', '') for i in f if not i.startswith('#') and len(i.replace('\n', '')) > 0 and i.endswith(form+'\n')]
    download_link_list(link_list)




def commandline_run():
    #collect_playlist_from_link(sys.argv[1])
    download_m3u8(sys.argv[-1])


commandline_run()

