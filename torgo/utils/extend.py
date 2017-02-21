#coding:utf-8

'''
Created on 2017年2月15日
@author: shuai.chen
'''

import time
from threading import RLock


__all__ = ['Odict', 'ExpireDict', 'DiffExpireDict']

class Odict(dict):
    """
    对字典进行扩展，使其支持通过 dict.a形式访问以代替dict['a']
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):
        return '<Odict ' + dict.__repr__(self) + '>'


class _Edict(dict):
    
    def __len__(self):
        return len(self.items())
    
    def __repr__(self):
        return '<{0} {1}>'.format(self.__class__.__name__ ,dict.__repr__(dict(self.items())))

    def update(self, obj):
        if isinstance(obj, self.__class__):
            super(_Edict, self).update(obj)
        else:
            raise TypeError("Type mismatch with %s" % self.__class__.__name__)  
 
    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
    
    def items(self):
        ditems = []
        for key in self.copy():
            value = self.get(key)
            if value is not None:
                ditems.append((key,value))
        return ditems

    def keys(self):
        return [key for key in self.copy() if key in self]
     
    def values(self):
        dvalues = []
        for key in self.copy():
            value = self.get(key)
            if value is not None:
                dvalues.append(value)
        return dvalues

    def iteritems(self):
        for key in self.copy():
            value = self.get(key)
            if value is not None:
                yield key,value
                
    def iterkeys(self):
        for key in self.copy():
            if key in self:
                yield key    
                
    def itervalues(self):
        for key in self.copy():
            value = self.get(key)
            if value is not None:
                yield value          
                
class ExpireDict(_Edict):
    """
    带有相同生命周期的字典扩展类
    """
    
    def __init__(self, expire=0):
        self.expire = max(0, expire)
        self.lock = RLock()
        
        super(ExpireDict,self).__init__()   
        
    def __get(self, key):    
        return super(ExpireDict, self).__getitem__(key)
    
    def __contains__(self, key):
        try:
            with self.lock:
                item = self.__get(key)
                if self.expire <= 0:
                    return True
                
                if int(time.time()) - item[1] < self.expire:
                    return True
                else:
                    del self[key]
        except KeyError:
            pass
        return False
    
    def __getitem__(self, key):
        with self.lock:
            item = self.__get(key)
            if self.expire <= 0:
                return item[0]

            if int(time.time()) - item[1] < self.expire:
                return item[0]
            else:
                del self[key]
                raise KeyError(key)
    
    def __setitem__(self, key, value):
        with self.lock:
            super(ExpireDict, self).__setitem__(key, (value, int(time.time())))
                
    def ttl(self, key):
        try:
            with self.lock:
                if self.expire <= 0:
                    return -1
                item = self.__get(key)
                key_ttl = self.expire - (int(time.time()) - item[1])
                if key_ttl > 0:
                    return key_ttl
                else:
                    del self[key]
        except:
            pass            
        return None

    def pop(self, key, default=None):
        with self.lock:
            try:
                item = self.__get(key)
                del self[key]
                return item[0]
            except KeyError:
                return default
             

class DiffExpireDict(_Edict):
    """
    带有不同生命周期的字典扩展类
    @example:
        d=DiffExpireDict()
        d['a'] = 1,7 # value,expire
        print d
    """
    def __init__(self):
        self.lock = RLock()
        
        super(DiffExpireDict,self).__init__()       

    def __get(self, key):    
        return super(DiffExpireDict, self).__getitem__(key)
            
    def __contains__(self, key):
        try:
            with self.lock:
                item = self.__get(key)
                if item[2] <= 0:
                    return True
                
                if int(time.time()) - item[1] < item[2]:
                    return True
                else:
                    del self[key]
        except KeyError:
            pass
        return False
    
    def __getitem__(self, key):
        with self.lock:
            item = self.__get(key)
            if item[2] <= 0:
                return item[0]

            if int(time.time()) - item[1] < item[2]:
                return item[0]
            else:
                del self[key]
                raise KeyError(key)
    
    def __setitem__(self, key, (value, expire)):
        with self.lock:
            expire = max(0, expire)
            super(DiffExpireDict, self).__setitem__(key, (value, int(time.time()), expire))    
                    
    def ttl(self, key):
        try:
            with self.lock:
                item = self.__get(key)
                if item[2] <= 0:
                    return -1
                key_ttl = item[2] - (int(time.time()) - item[1])
                if key_ttl > 0:
                    return key_ttl
                else:
                    del self[key]
        except:
            pass            
        return None

    def pop(self, key, default=None):
        with self.lock:
            try:
                item = self.__get(key)
                del self[key]
                return item[0]
            except KeyError:
                return default
            