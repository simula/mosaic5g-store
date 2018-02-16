import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import threading
from threading import Timer
import time
import visualize


class visualize(object):
	_linewidth=2.0
	_title=' '
	_ylabel=' '
	_xlabel=' '
	_ms=6.0
	_label='legend'
	_xylim=None
	_window_size=None
	_plot_var_window=[]
	_plot_type='simple'
	_fig=None
	_ax1=None
	_created=False
	_p1=None
	_new_fig=False
	_animate_thread_handle = None
	_binwidth=7

	name="visualize"

	def __init__(self,window_size,new_fig=False) :
		self._window_size=window_size
		self._new_fig=new_fig
		#self._plot_var_window=[np.nan]*window_size
		self._plot_var_window=[0]*window_size
		self._created = False

	def create(self,plot_type,fig_num):
		self._plot_type=plot_type
		self._fig = plt.figure()
		self._ax1 = self._fig.add_subplot(1,1,1)
		ani = animation.FuncAnimation(self._fig, self._animate, interval=500)
		plt.show()

	def remove(self):
		plt.close(self._fig)
		print "figure go bye bye..."


	def update(self,ys):
		num_samples_in_plot = 100
		self._plot_var_window.insert(0,ys)
		#self._plot_var_window = np.random.normal(0, 1, num_samples_in_plot)
		del self._plot_var_window[self._window_size:]

	def _animate(self,i):
		ys = self._plot_var_window
		self._ax1.clear()
		if not all(x == np.nan for x in self._plot_var_window):
			if self._plot_type == 'simple' : 
				self._ax1.plot(ys)
			elif self._plot_type == 'hist' :
				print "hist plot"
				#self._ax1.hist(ys[~np.isnan(ys)])
				self._ax1.hist(ys, bins=range(min(ys), max(ys) + self._binwidth, self._binwidth))
		else :
			print "Waiting for first update in data"



def loop_over_data(t):
	num_samples_in_plot = 100
	ys = np.random.normal(0, 1, 1)
	viz.update(ys)
	tim = Timer(t, loop_over_data,kwargs=dict(t=t))
	tim.start()


if __name__ == '__main__':
	num_samples_in_plot = 100
	timer_period_s = 0.05 
	print ("started timer with period " + str(timer_period_s) + ' s')
	tim = Timer(timer_period_s, loop_over_data,kwargs=dict(t=timer_period_s))
	tim.start()
	viz = visualize(num_samples_in_plot,True)
	viz.create(plot_type='simple',fig_num=1)
	#viz.create(plot_type='simple',fig_num=2)
	#viz2.create(plot_type='simple')




