import numpy as np
import matplotlib.pyplot as plt

data = np.genfromtxt('file.csv', delimiter=' ',names=['x','u','f1final','umax','maxumax','window','not_ack','avRtt','refRtt','lref','Rtt1','Rtt2','idle'],skip_footer=1)

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.plot(data['x'], data['avRtt'], color='r', label='the data')

ax2 = fig.add_subplot(111)
#ax2.plot(data['x'], data['minRtt'], color='b', label='the data')
ax2.plot(data['x'], data['lref'], color='g', label='the data')
ax2.plot(data['x'], data['refRtt'], color='m', label='the data')

fig2 = plt.figure()
ax21 = fig2.add_subplot(111)
ax21.plot(data['x'], data['u'], color='r', label='the data')

ax22 = fig2.add_subplot(111)
ax22.plot(data['x'], data['window'], color='b', label='the data')
ax22.plot(data['x'], data['maxumax'], color='y', label='the data')
ax22.plot(data['x'], data['umax'], color='m', label='the data')
fig3 = plt.figure()
ax31 = fig3.add_subplot(111)
ax31.plot(data['x'], data['idle'], color='r', label='the data')
#ax31.plot(data['x'], data['Rtt2'], color='b', label='the data')
#ax31.plot(data['x'], data['ferror'], color='g', label='the data')
plt.show()