_script="$(readlink -f ${BASH_SOURCE[0]})"

## Delete last component from $_script ##
_mydir="$(dirname $_script)"


source ${_mydir}/../../bin/activate
export RHOMBUS_CONFIG=${_mydir}/development.ini
export PATH=${_mydir}/libexec:${PATH}
