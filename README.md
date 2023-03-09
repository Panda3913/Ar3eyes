# AR3 (By python)
## For python3
### **About**

| About     | Content               |
| ----------| ----------------------|
| author    | timmy (WeiWen Wu)     |
| date      | 2022/11/21            |
| version   | 2.0  (for python3 )   |

### **Package**
* serial (pyseial)
* time
* multiprocessing、threading
* (pyfirmata2) => can not

### **Tutorial**
1. [G-code](https://kknews.cc/zh-tw/tech/39k2xx3.html) 
2. [pyseial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)

### **Function** 
#### **setting**
| Variable                      | Default                   |
| ------------------------------| --------------------------|
| serial_port_auto              | True                      |
| serial_port_auto_get_count    | 10                        |
| joint_angle_limit             | [360,360,360,360,360,360] |
| standard_posture              | [240,30,30,85,165,155]    |
| join_count                    | 6                         |
| warning                       | False                     |
| set_one_absolute_info         |  True                     |


### **Use** 

```python
# for python
from pyar3 import AR3_py3
arm = AR3_py3.AR3() 
       
arm.set_all([0,0,0,0,0,0])
ar3.set_all([90,90,90,90,90,90])
print(arm.get_all())

arm.close()
```

---------------
---------------

## For python2
### **About**
| about | detail |
| ---- | ----|
| author | timmy (WeiWen Wu) |
| date | 2022/9/7 |
| version | 1.0 (for python2 ) |

### **Package**
* serial (pyseial)
* time
* multiprocessing、threading
* (pyfirmata2) => can not

