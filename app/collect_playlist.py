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
import tempfile
from shutil import copyfile
import ssl

from config import basedir
  

#result_file = 'result.mkv'

path = basedir+'/tmp/'

log_filename = path+'/mkv_log.txt'

form = '.ts'

def download_video(idx, epoch, targetLink):
    start = time.time()

    url = urllib.parse.urlparse(targetLink)

    con = hc.HTTPSConnection(url.netloc)
    #targetUrl = url.path+';'+url.params+'?'+url.query+'#'+url.fragment
    targetUrl = url.path
    if url.params:
        targetUrl += ';'+url.params
    if url.query:
        targetUrl += '?'+url.query
    if url.fragment:
        targetUrl += '#'+url.fragment

    con.request('GET', targetUrl)
    res = con.getresponse()
    #print(res, res.status, res.reason, res.headers)
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
    ssl._create_default_https_context = ssl._create_unverified_context

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

    os.remove(log_filename)

    for chunk_id in range(lsize):
        os.system("mkvmerge -o "+path+"res_"+str(chunk_id)+".mkv '[' "+' '.join(sorted_list[chunk_id*chunk:(chunk_id+1)*chunk])+" ']'"+" >> "+log_filename)
        #print("mkvmerge -o "+path+"res_"+str(chunk_id)+".mkv '[' "+' '.join(sorted_list[chunk_id*chunk:(chunk_id+1)*chunk])+" ']'")
    os.system("mkvmerge -o "+path+"res_"+str(lsize)+".mkv '[' "+' '.join(sorted_list[(lsize-1)*chunk:])+" ']'"+" >> "+log_filename)

    res_list = sorted([path+fn for fn in os.listdir(path) if fn.endswith('.mkv') and fn.startswith('res_')], key=lambda x: int(x.split('/')[-1].split('.')[0].split('_')[-1]))
    #print(res_list)

    os.system("mkvmerge -o "+result_file+" '[' "+' '.join(res_list)+" ']'"+" >> "+log_filename)
    #print("mkvmerge -o result.mkv '[' "+' '.join(res_list)+" ']'")

    for i in sorted_list:
        os.remove(i)
    for i in res_list:
        os.remove(i)



    end = time.time()
    print('Collect time :', end-start)


def collect_playlist_from_link(targetLink):


    url = urllib.parse.urlparse(targetLink)

    con = hc.HTTPSConnection(url.netloc)
    targetUrl = url.path+';'+url.params+'?'+url.query+'#'+url.fragment

    con.request('GET', targetUrl)
    res = con.getresponse()
    body = res.read()

    print(res.status, res.reason, res.msg)

    #print(body)

    link_list = [i for i in body.decode('utf-8').split('\n') if not i.startswith('#') and len(i) > 0]

    download_link_list(link_list)
    

def collect_playlist_from_file(file_name):
    f = open(file_name, 'r')
    link_list = [i.replace('\n', '') for i in f if not i.startswith('#') and len(i.replace('\n', '')) > 0 and i.endswith(form+'\n')]
    download_link_list(link_list)


#res = collect_playlist_from_link('https://vh-04.getcourse.ru/player/99c72a16d1348a3a870e9caae82dcd69/b59a8a6cbd6d8d7e8009586468434a6a/media/720.m3u8?sid=&host=vh-12&cdn=1&cdn-second=0&integros-s3=0&akamai-defence=0&v=2:2:1:1')

#res = collect_playlist_from_link("https://vh-04.getcourse.ru/player/11ee6e312c9cc6f118bc3a207d0a5cda/52f06734900fde8fae4598254d1d6d1d/media/720.m3u8?sid=sid&host=vh-26&user-cdn=&akamai-cdn-pr=0&v=2:2:1:1")

