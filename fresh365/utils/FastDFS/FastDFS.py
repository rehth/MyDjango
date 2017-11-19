from fdfs_client.client import Fdfs_client
from django.core.files.storage import Storage
from django.conf import settings


# 储存类必须实现 _open()/返回File对象/ 和 _save()/返回被保存文件的真实名称/方法，以及任何适合于你的储存类的其它方法
class FDFSStorage(Storage):
    def __init__(self, server_url=None, conf_client=None):
        self.server_url = server_url
        self.conf_client = conf_client
        if not server_url:
            self.server_url = settings.FDFS_SERVER_URL
        if not conf_client:
            self.conf_client = settings.FDFS_CONF_CLIENT

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        # content自己必须是一个File对象
        client = Fdfs_client(conf_path=self.conf_client)
        ret = client.upload_by_buffer(content.read())
        """
        dict
        {
            'Group name': group_name,
            'Remote file_id': remote_file_id,
            'Status': 'Upload successed.',
            'Local file name': '',
            'Uploaded size': upload_size,
            'Storage IP': storage_ip
        } if success else None
        """
        # 如果上传失败则抛出异常
        if not ret['Status'] == 'Upload successed.':
            raise Exception('FastDFS Upload Fail')
        # 返回被保存文件的真实名称
        return ret.get('Remote file_id')

    def exists(self, name):
        # 提供的名称所引用的文件在文件系统中存在，则返回True，
        # 否则如果这个名称可用于新文件，返回False
        return False

    def url(self, name):
        return self.server_url + name

