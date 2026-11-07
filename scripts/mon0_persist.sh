#!/bin/sh
printf '#!/bin/sh\niw phy phy0 interface add mon0 type monitor 2>/dev/null || true\nip link set mon0 up\n' > /etc/local.d/mon0.start
chmod 755 /etc/local.d/mon0.start
rc-update add local default
rc-service local start
iw dev mon0 info
echo PERSIST_OK
