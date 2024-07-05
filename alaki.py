#
# 
#

res = []
for dns in dnses:
    intersect = [dns.getRole(ip) for ip ]
