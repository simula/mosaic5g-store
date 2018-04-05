"""
   Licensed to the Mosaic5G under one or more contributor license
   agreements. See the NOTICE file distributed with this
   work for additional information regarding copyright ownership.
   The Mosaic5G licenses this file to You under the
   Apache License, Version 2.0  (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
  
    	http://www.apache.org/licenses/LICENSE-2.0
  
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
 -------------------------------------------------------------------------------
   For more information about the Mosaic5G:
   	contact@mosaic-5g.io
"""

"""
    File name: app_sdk.py
    Author: Lukasz Kulacz and navid nikaein
    Description: This lib provides APIs for a control app to visualize data in different format
    version: 1.0
    Date created:  22 Fev 2018
    Date last modified: 22 Fev 2018
    Python Version: 2.7
    ToDo: support multi-line plots. Beautify a figure, 
    
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
from enum import Enum

class FigureType(Enum):
	Bar='bar'
	Plot='plot'
	Rect='rect'

class Color(Enum):
	Yellow='y'
	Magenta='m'
	Cyan='c'
	Red='r'
	Green='g'
	Blue='b'
	White='w'
	Black='k'

class LineType(Enum):
	Solid='-'
	Dashed='--'
	Dotted=':'
	DashDot='-.'

class Figure:
	def __init__(self, name, rows, cols, figsize):
		self.__name = name
		self.__rows = rows
		self.__cols = cols
		self.__rects = [0]*(rows*cols)
                self.__lines = 0
		fig, axes = plt.subplots(rows, cols, figsize=figsize)
		fig.suptitle(name, fontsize=14)
		if rows == 1 and cols == 1:
			self.__axes = [axes]
		elif rows == 1 or cols == 1:
			self.__axes = axes
		else:
			self.__axes = axes.flatten('F')
		self.__fig = fig
		plt.show()

	def get_index(self, row, col, message):
		i = (col-1)*(self.__rows) + (row - 1)
		if i >= self.__rows * self.__cols:
			print('wrong index (too high) ' + str(message))
			return 0
		else:
			return i

	def clear(self, row, col):
		index = self.get_index(row, col, 'clear')
		self.__axes[index].cla()
		#self.update()

	def show(self, row, col, x, y, fig_type, fill, autoscale):
		index = self.get_index(row, col, 'show')
		if type(fig_type) is str:
		    	fig_type = FigureType(fig_type)
		if not type(fig_type) is FigureType:
			print('fig_type must by "FigureType" class object')
			return
		if fig_type == FigureType.Plot:
			self.__axes[index].plot(x,y)
		elif fig_type == FigureType.Bar:
			self.__rects[index] = self.__axes[index].bar(x,y)
		elif fig_type == FigureType.Rect:
			self.__axes[index].add_patch(patches.Rectangle(x, y[0], y[1], fill=fill, linewidth=2))		
			if autoscale:
				self.__axes[index].autoscale()
		
		#self.update()

	def append(self, row, col, x_step, y, fig_type):
		old_x, old_y = self.get_data(row, col, fig_type)
		
		new_x = np.append(old_x, old_x[-1]+x_step)
		new_y = np.append(old_y, y)
		self.clear(row, col)
		self.show(row, col, new_x, new_y, fig_type, False, False)	
		#self.update()

	def get_data(self, row, col, fig_type):
		index = self.get_index(row, col, 'append')
		if type(fig_type) is str:
		    	fig_type = FigureType(fig_type)
		if not type(fig_type) is FigureType:
			print('fig_type must by "FigureType" class object')
			return None
		if fig_type == FigureType.Plot:
			if len(self.__axes[index].lines) == 0:
				print('cannot append to empty plot!')
				return None
			old_x = self.__axes[index].lines[0].get_xdata()
			old_y = self.__axes[index].lines[0].get_ydata()
		elif fig_type == FigureType.Bar:
			if len(self.__rects[index]) == 0:
				print('cannot append to empty plot!')
				return None
			old_x = []
			old_y = []
			for rect in self.__rects[index]:
				old_x.append(rect.xy[0]+rect.get_width()/2.0)
				old_y.append(rect.get_height())
		elif fig_type == FigureType.Rect:
			print ('for rect type of plot use "show" istead')
			return None
		return (old_x, old_y)
		

	def legend(self, row, col, args):
		index = self.get_index(row, col, 'legend')
		self.__axes[index].legend(args)	
		#self.update()

	def beautify(self, row, col, color, line, xlabel, ylabel, title, grid, index, fig_type):
		ind = self.get_index(row, col, 'beautify') # only for check if too high
		i = (row-1)*(self.__cols) + (col - 1)
	
		if not xlabel is None:
			self.__axes[ind].set_xlabel(xlabel)
		if not ylabel is None:
			self.__axes[ind].set_ylabel(ylabel)
		if not title is None:
			self.__axes[ind].set_title(title)

		if not grid is None:
			self.__axes[ind].grid()

		if type(fig_type) is str:
		    	fig_type = FigureType(fig_type)

		if not color is None:
			if type(color) is Color:
				if fig_type == FigureType.Plot:
					self.__axes[ind].lines[index-1].set_color(color.value)
				elif fig_type == FigureType.Bar:
					self.__rects[ind][index].set_color(color.value)
			elif type(color) is tuple or type(color) is list:
				if len(color) == 3 or len(color) == 4:
					if fig_type == FigureType.Plot:
						self.__axes[ind].lines[index-1].set_color(color)
					elif fig_type == FigureType.Bar:
						self.__rects[ind][index].set_color(color.value)
				else:
					print('wrong length of color. Provide 3 or 4 (RGB, RGBA)')
			else:
				print('Color type error. Provide Color object or RGB tuple or RGBA tuple.')
		if not line is None:
			if type(line) is LineType:
				if fig_type == FigureType.Plot:
					self.__axes[ind].lines[index-1].set_linestyle(line.value)
				else:
					print('cannot change line style (wrong figure type)')
		#self.update()
		

	def axis(self, row, col, args):
		index = self.get_index(row, col, 'axis')
		self.__axes[index].axis(args)	

	def close(self):
		plt.close(self.__fig)

	def save(self, filename, dpi, fig_format):
		self.__fig.savefig(filename, dpi=dpi, format=fig_format)

	def update(self):
		self.__fig.canvas.draw()


class FigureManager:
	def __init__(self):
		self.figs = {}
		plt.ion()

	def create(self, name='default', rows=1, cols=1, figsize=(8.8,8.8)):
		if name in self.figs.keys():
			print('Cannot create - name is in use.')
		else:
			self.figs[name] = Figure(name, rows, cols, figsize)

	def clear(self, name='default', row=1, col=1):
		if name in self.figs.keys():
			self.figs[name].clear(row, col)
		else:
			print(str(name)+ ' not found - clear function')

	def show(self, x, y, name='default', row=1, col=1, clear=False, fill=False, autoscale=True, fig_type=FigureType.Plot):
		if name in self.figs.keys():
			if clear:
				self.figs[name].clear(row, col)
			self.figs[name].show(row, col, x, y, fig_type, fill, autoscale)			
		else:
			print(str(name) + ' not found - show function')
	
	def legend(self, args, name='default', row=1, col=1):
		if name in self.figs.keys():
			self.figs[name].legend(row, col, args)

	def beautify(self, name='default', row=1, col=1, color=None, line=None, xlabel=None, ylabel=None, title=None, grid=None, line_index=0, fig_type=FigureType.Plot):
		if name in self.figs.keys():
			self.figs[name].beautify(row, col, color, line, xlabel, ylabel, title, grid, line_index, fig_type)

	def append(self, y, x_step=1, name='default', row=1, col=1, fig_type=FigureType.Plot):
		if name in self.figs.keys():
			self.figs[name].append(row, col, x_step, y, fig_type)

	def axis(self, args, name='default', row=1, col=1):
		if name in self.figs.keys():
			self.figs[name].axis(row, col, args)

	def close(self, name='default'):
		if name in self.figs.keys():
			self.figs[name].close()
			del self.figs[name]	

	def save(self, name='default', filename='save', dpi=90, fig_format='png'):
		if name in self.figs.keys():
			self.figs[name].save(filename, dpi, fig_format)	

	def update(self, name='default'):
		if name in self.figs.keys():
			self.figs[name].update()		
		
if __name__ == "__main__":
	fm = FigureManager()

	fm.create(cols=3, rows=2)
	
	time.sleep(1)
	#xy_origin=(5,3), x_target+=2, y_target+=1 
	
	fm.show((5, 3), [2, 1], col=3, row=2, fig_type=FigureType.Rect)
	
	fm.show((1, 1), [1, 1], col=3, row=2, fig_type=FigureType.Rect, fill=True)
        # x and y array
	
	fm.show([1, 2, 3, 4], [2, 2, 3, 5], col=2)
	fm.beautify(col=2, row=1, color=(0.8,0,0), line=LineType.DashDot, xlabel='x', ylabel='y', title='title', grid=True)
	
        # x and y array
	fm.show([1, 2, 3], [231, 211, 243], col=1, row=2, fig_type=FigureType.Bar)
        # y for x+=x_step
	fm.append(200, x_step=2, col=1, row=2, fig_type=FigureType.Bar)

	fm.beautify(col=1, row=2, color=Color.Red, fig_type=FigureType.Bar, grid=True)
	
	time.sleep(10)
        # x and y array 
	fm.show(x=[2, 4], y=[21, 2], col=2, row=2)
	fm.show(x=[3, 5], y=[15, 4], col=2, row=2)
	# append y for x+=1
        time.sleep(10)
        # append clear the fig before redrawing it, 
	fm.append(15, col=2, row=2)
        fm.append(10, col=2, row=2)
	
	time.sleep(10)
	
	fm.axis([-2, 5, 0, 30], col=1, row=1)

	time.sleep(1)

