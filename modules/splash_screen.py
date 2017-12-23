from time import sleep
from getpass import getuser
from modules.clear_screen import *

def display_splash_screen():
    clear()
    logo = '''\n\n\n\x1b[1m\x1b[37m                              `.-:/+oosssssshmo/:-.`                   
                         `-/osssssssssssssssdNysssso/-`               
                      .:osssssssssssssssssssshNhssssssso/.            
                   `-ossssssssssssssssssssssssyNdssssssssso:`         
                 `:ssssssss+:::+sssssssssssssssyNmsssssssssss:`       
                +hdddddddy`     .dddddddddddddddmMNysssssssssss-      
              `+yyyyyyyyy/       dMMMMMMMMMMMMMMMMMNysssssssssss+`    
             `osssssssssss:     +MMMMMMMMMMMMMMMMMMMMhssssssssssso.   
            .osssssssssssdMNhyhNMMMMMMMMMMMMMMMMMMMMMMdssssssssssss.  
           `osssssssssssmMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMdssssssssssdm. 
           +ssssssssssymMh+dMMMMMMMosNMMMMMMd+dMMMMMMMMMmysssssssmNy+ 
          .ssssssssssyNMMN+`:dMMMMMh-`sNMMMMNo`:hMMMMMMMMNyssssymmsss-
          /sssssssssyNMMMMMNo`:dMMMMMh-`sNMMMMNo`-hMMMMMMMNhssyNmssss+
          osssssssshMMMMMMMMMNo`:dMMMMMh-`sNMMMMNo`-hMMMMMMMhyNdssssss
          ssssssssdMMMMMMMMMMMMNo`:mMMMMMh-`oMMMMMNo`-dMMMMMMMhsssssss
          sssssssmNMMMMMMMMMMMMN+`:mMMMMMd:`oMMMMMNs`-hMMMMMMhssssssss
          ossssymmyhMMMMMMMMMN+`:dMMMMMd:`oNMMMMNs`-hMMMMMMNysssssssss
          /sssyNmsssyNMMMMMm+`/dMMMMMd:`oNMMMMNs`-hMMMMMMMNysssssssss+
          .ssyNdsssssyNMMN+`/dMMMMMd:`oNMMMMMo`-hMMMMMMMMNyssssssssss.
           /hNhssssssssmMd+dMMMMMMMooNMMMMMMm+hMMMMMMMMMmsssssssssss+ 
           .dhssssssssssdMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMmssssssssssso` 
            `ossssssssssshMMMMMMMMMMMMMMMMMMMMMMMMMMMMdssssssssssss.  
             `osssssssssssyNMMMMMMMMMMMMMMMMMMMMMMMMMhssssssssssso`   
               +sssssssssssyNMMMMMMMMMMMMMMMMMMMMMMMdyyyyyyyyyyy+`    
                -ossssssssssymMmddddddddddddddddddddddddddddddh/      
                  :ossssssssssdNyssssssssssssssssssssssssssss:`       
                    -+ssssssssshNhsssssssssssssssssssssssso-`         
                      `:ossssssshNdsssssssssssssssssssso:.            
                         `-/ossssyNdssssssssssssssso/-`               
                              `-:/+dhoossooo++/:-`\x1b[0m'''
    print logo
    print '\n\n\n                         \x1b[1m\x1b[37mWelcome to Python-Iris, \x1b[0m\x1b[1m\x1b[31m'+getuser()+'\x1b[0m'
    sleep(5)