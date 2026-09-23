cmake_minimum_required(VERSION 3.0.2)
project(vs_practice)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
  trajectory_msgs
  cv_bridge
  tf
  moveit_msgs
)

catkin_python_setup()
catkin_package()

catkin_install_python(PROGRAMS
  scripts/print_interface.py
  scripts/vs_detect_node.py
  scripts/vs_servo_node.py
  scripts/vs_commander_node.py
  scripts/vs_fsm_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
