To deploy and test:
```
# Copy to blue machine
scp blue_victim.py quanserblue@192.168.2.178:~/Documents/sros/sros/red_blue_1/

# On blue machine — run WITHOUT security first to confirm it still works normally
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py

# Then run WITH security enabled
export ROS_SECURITY_KEYSTORE=~/sros2_keystore
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
python3 ~/Documents/sros/sros/red_blue_1/blue_victim.py
```
Then from red machine run rogue_node.py and watch for silence on blue.
