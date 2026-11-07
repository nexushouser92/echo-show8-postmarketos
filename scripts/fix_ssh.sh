passwd -d root
passwd -d kali 2>/dev/null || true
sed -i '/PermitRootLogin/d' /etc/ssh/sshd_config
sed -i '/PermitEmptyPasswords/d' /etc/ssh/sshd_config
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "PermitEmptyPasswords yes" >> /etc/ssh/sshd_config
grep -E "PermitRoot|PermitEmpty" /etc/ssh/sshd_config
rc-service sshd restart
echo "SSH_FIXED"
