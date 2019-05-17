import pymongo
import requests 
import os 
import sys 

from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import re 
from threading import Thread

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

# class Logger(object):
#     def __init__(self, filename="Default.log"):
#         self.terminal = sys.stdout
#         self.log = open(filename, "a")
 
#     def write(self, message):
#         self.terminal.write(message)
#         self.log.write(message)
 
#     def flush(self):
#         pass
# path = os.path.abspath(os.path.dirname(__file__))
# type = sys.getfilesystemencoding()
# sys.stdout = Logger('download_log.txt')


class Download(object):
    def __init__(self):
        self.headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
        }
        self.error_count = 0

    def parse_cryptor(self,url,file_lines):
        """
            从key_url中获取密钥并返回
        """
        try:
            for line in file_lines:
                # 找解密Key
                if "#EXT-X-KEY" in line: 
                    method_pos = line.find("METHOD")
                    comma_pos = line.find(",")
                    method = line[method_pos:comma_pos].split('=')[1]
                    print ("Decode Method：", method)
                    uri_pos = line.find("URI")
                    quotation_mark_pos = line.rfind('"')
                    key_path = line[uri_pos:quotation_mark_pos].split('"')[1]
                    # key解密密钥URL
                    key_url = url.rsplit("/", 1)[0] + "/" + key_path # 拼出key解密密钥URL
                    res = requests.get(key_url,headers=self.headers,timeout=10)
                    key = res.content
                    if len(key): # AES 解密
                        cryptor = AES.new(key, AES.MODE_CBC, key) 
                        return cryptor
            return None 
        except Exception as e:
            print('错误：',e)
            return None

    def conn_db(self,ip,port,db_name,collection):
        # 创建Mongo数据库连接对象
        conn = pymongo.MongoClient(ip,port)
        #创建数据库操作对象
        db = conn[db_name]
        movie_set = db[collection]
        return movie_set

    def get_res(self,url):
        """
            获取url请求中的内容 
        """
        content = requests.get(url,headers=self.headers).content
        return content

    def get_all_content(self,url):
        try:
            all_content = requests.get(url,headers=self.headers,timeout=10).text
        except:
            return None 
        file_line = all_content.split("\n")
        for line in file_line:
            if '.m3u8' in line:
                url = url.rsplit("/", 1)[0] + "/" + line # 拼出第二层m3u8的URL
                all_content = requests.get(url,timeout=10).text
                return url,all_content
        return None

    def mkdirs(self,path):
        """
            如果目录不存在，则创建
        """
        if not os.path.exists(path):
            os.makedirs(path)
            return True 
        return False

    def get_ts_url(self,url,file_lines):
        try:
            # urls = []
            for index, line in enumerate(file_lines): # 第二层
                if "EXTINF" in line: # 找ts地址并下载
                    pd_url = url.rsplit("/", 1)[0] + "/" + file_lines[index + 1] # 拼出ts片段的URL
                    yield pd_url
        except Exception as e:
            return None

    def get_ts(self,ts_url,name,ts_list,path):
        global error_count
        try:
            # if self.error_count>=3:
                # print('下载：{} ,出错超过三次'.format(ts_url))
                # sys.exit()
            print("下载：ts 片段 ",ts_url)
            serial_number = re.findall("(\d+).ts",ts_url)[-1]
            res = requests.get(ts_url,headers = self.headers,timeout=2)
            ts_list.append({'serial_number':int(serial_number),'res':res})
        except Exception as e:
            print("出错：",path,self.error_count,e)
            self.error_count+=1
            # print(error_count)
            # get_ts(ts_url,name,ts_list,error)



    def is_exists(self,file_name):
        """
            判断文件是否存在
        """
        if os.path.isfile(file_name) and os.path.getsize(file_name):
            return True 
        else:
            return False 


    def load_locally_video(self,ts_list,title,dir_path,cryptor):
        """
            将视频写入到本地 
        """
        try:
            ts_infos = sorted(ts_list,key=lambda x:x['serial_number'])
            print(ts_infos)
            with open(os.path.join(dir_path, title+".mp4"), 'ab') as f:
                for ts_info in ts_infos:
                    res = ts_info['res']
                    try:
                        f.write(cryptor.decrypt(res.content))
                    except Exception as e:
                        # 如果下载下来的视频有问题，请注释掉本行
                        f.write(res.content)
                        # self.err_log.write(str(e))
                        print('warning：',e)
                        continue
            return True
        except Exception as e:
            # self.err_log.write(str(e))
            print('未知错误：',e)
            return False

    def write_img(self,url,title,dir_path,error=0):
        try:
            if error>=3:
                print("下载： {} 超过3次，停止下载".format(url))
                return
            img_path = os.path.join(dir_path,title+".png")
            if not self.is_exists(img_path):
                img = requests.get(url,headers=self.headers).content 
                with open(img_path,'wb') as f:
                    f.write(img)
            else:
                print("图片 {} 已经存在".format(img_path))
                return 
        except:
            error+=1
            self.write_img(url,title,dir_path,error)
    

    def start(self,thread_count,movie_info):
        # 图片url
        cover_url = movie_info['cover']
        # 写入的地址
        dir_path = movie_info['movie_path']
        # 名称
        title = re.sub(r"\..*","",movie_info['title'])
        # 开始写入图片
        # t = Thread(target=write_img,args=(cover_url,title,dir_path))
        # t.start()
        # 获取视频信息
        p = ThreadPoolExecutor(thread_count)
        ts_list  = []
        if self.is_exists(os.path.join(dir_path, title+".mp4")):
            print("视频 {} 已经存在".format(os.path.join(dir_path, title+".mp4")))
            return 
        m3u8_url = movie_info['dowload_link']
        try:
            # 获取m3u8和所有文件内容
            url,all_content = self.get_all_content(m3u8_url)
        except:
            url = m3u8_url 
            try:
                all_content = requests.get(m3u8_url,headers=self.headers,timeout=10).text
            except Exception as e:
                print('获取下载连接失败：',e)
                return 
            print(all_content)
            
        print('正在下载【{0}】类型的视频：【{1}】 url  {2} '.format(movie_info["type"][0],title,url) )
        # 将m3u8的文件内容按换行分割
        file_lines = all_content.split('\n')
        # 获取密钥
        cryptor = self.parse_cryptor(url,file_lines)
        # global error_count
        # print(file_lines)
        for index,ts_url in enumerate(self.get_ts_url(url,file_lines)):
            # print(ts_url)
            # continue   
            # 失败太多次，直接结束进程
            # print(self.error_count)
            # if self.error_count>=3:
            #     return 
            name = " {} 号下载线程".format(index)
            p.submit(self.get_ts,ts_url,name,ts_list,dir_path)
        p.shutdown() 
        if ts_list:
            # 保存视频到本地
            if self.load_locally_video(ts_list,title,dir_path,cryptor):
                print('下载视频完成 {} '.format(os.path.join(dir_path, title+".mp4")))


if __name__ == "__main__":
    process_count = 2
    thread_count = 16
    base_dir = r"/samba/av"
    dowload_link_list = []
    download = Download()
    movie_set = download.conn_db('39.106.118.34',27017,'welfareFilm','movie')
    pool = Pool(processes = process_count)
    blacklist = ["美女主播"]
    for movie_info in movie_set.find({},{'_id':0})[1:]:
        if movie_info['dowload_link'] in dowload_link_list:
            continue
        else:
            dowload_link_list.append(movie_info['dowload_link'])
        if movie_info['type'][0] in blacklist:
            continue
        # title = re.sub(r"\..*","",movie_info['title'])
        # dir_name = movie_info['release_date']+title
        # 拼接视频存储目录
        movie_path = os.path.join(base_dir,movie_info['type'][0])
        # 创建下载目录
        # movie_path = re.sub('[\/:、：*?"<>|]','-',movie_path)#去掉非法字符 
        download.mkdirs(movie_path)
        movie_info['movie_path'] = movie_path
        # download.start(thread_count,movie_info)
        pool.apply_async(download.start,(thread_count,movie_info))
        # break 

    pool.close()
    pool.join()  