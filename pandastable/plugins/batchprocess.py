#!/usr/bin/env python
"""
    File rename utility.
    Created January 2012
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from __future__ import absolute_import, division, print_function
try:
    from tkinter import *
    from tkinter.ttk import *
    from tkinter.scrolledtext import ScrolledText
except:
    from Tkinter import *
    from ttk import *

if (sys.version_info > (3, 0)):
    from tkinter import filedialog, messagebox, simpledialog
else:
    import tkFileDialog as filedialog
    import tkSimpleDialog as simpledialog
    import tkMessageBox as messagebox
    from ScrolledText import ScrolledText
import os, string, time
import re, glob
import pandas as pd
from pandastable.plugin import Plugin
from pandastable import Table, TableModel, dialogs
import pylab as plt

class MyTable(Table):
    """
      Custom table class inherits from Table.
      You can then override required methods
     """
    def __init__(self, parent=None, **kwargs):
        Table.__init__(self, parent, **kwargs)
        return

    def handle_right_click(self, event):
        """respond to a right click"""

        return

class BatchProcessPlugin(Plugin):
    """Batch processing plugin for DataExplore. Useful for multiple file import
    and plotting.
    """

    capabilities = ['gui','uses_sidepane']
    requires = ['']
    menuentry = 'Batch Process'
    gui_methods = {}
    version = '0.1'

    def __init__(self):
        return

    def main(self, parent):
        self.parent=parent
        if parent==None:
            self.main=Toplevel()
            self.master=self.main
            self.main.title('Batch Process')
            ws = self.main.winfo_screenwidth()
            hs = self.main.winfo_screenheight()
            w = 900; h=500
            x = (ws/2)-(w/2); y = (hs/2)-(h/2)
            self.main.geometry('%dx%d+%d+%d' % (w,h,x,y))
        else:
            self.parent = parent
            self._doFrame()
            self.main=self.mainwin
        self.doGUI()
        self.currentdir = os.path.expanduser('~')

        self.addFolder(path='test_batch')
        #self.test()
        return

    def doGUI(self):
        """Create GUI"""

        #self.m = PanedWindow(self.main,
        #                     orient=VERTICAL)
        #self.m.pack(side=LEFT,fill=BOTH,expand=1)

        frame = Frame(self.main)
        frame.pack(side=LEFT,fill=BOTH,expand=1)
        df = pd.DataFrame()
        self.pt = MyTable(frame, dataframe=df, read_only=1, showtoolbar=0, width=100)
        self.pt.show()
        #self.m.add(frame)
        fr = Frame(self.main, padding=(4,4), width=120)
        fr.pack(side=RIGHT,fill=BOTH)

        self.extensionvar = StringVar()
        w = Combobox(fr, values=['csv','tsv','txt','csv.gz','*'],
                 textvariable=self.extensionvar,width=6)
        w.pack(side=TOP,fill=BOTH,pady=2)
        w.set('csv')
        Label(fr,text='delimiter').pack()
        self.delimvar = StringVar()
        delimiters = [',',r'\t',' ',';','/','&','|','^','+','-']
        w = Combobox(fr, values=delimiters,
                 textvariable=self.delimvar,width=6)
        w.pack(side=TOP,fill=BOTH,pady=2)
        w.set(',')
        self.indexcolvar=IntVar()
        Label(fr,text='index column').pack()
        w=Entry(fr,textvariable=self.indexcolvar,width=6)
        w.pack(side=TOP,fill=BOTH,pady=2)
        b=Button(fr,text='Add Folder',command=self.addFolder)
        b.pack(side=TOP,fill=BOTH,pady=2)
        b=Button(fr,text='Clear',command=self.clear)
        b.pack(side=TOP,fill=BOTH,pady=2)
        self.recursivevar = BooleanVar()
        self.recursivevar.set(False)
        b=Checkbutton(fr,text='Load Recursive',variable=self.recursivevar)
        b.pack(side=TOP,fill=BOTH,pady=2)
        self.useselectedvar = BooleanVar()
        self.useselectedvar.set(False)
        b=Checkbutton(fr,text='Selected Only',variable=self.useselectedvar)
        b.pack(side=TOP,fill=BOTH,pady=2)
        b=Button(fr,text='Show Table',command=self.previewTable)
        b.pack(side=TOP,fill=BOTH,pady=2)
        b=Button(fr,text='Import All',command=self.importAll)
        b.pack(side=TOP,fill=BOTH,pady=2)
        b=Button(fr,text='Preview Plot',command=self.previewPlot)
        b.pack(side=TOP,fill=BOTH,pady=2)
        b=Button(fr,text='Run Batch Plots',command=self.batchPlot)
        b.pack(side=TOP,fill=BOTH,pady=2)

        table = self.parent.getCurrentTable()
        self.pf = table.pf
        return

    def addFolder(self, path=None):
        """Get a folder"""

        if path==None:
            path = filedialog.askdirectory(parent=self.main,
                                            initialdir=self.currentdir,
                                            title='Select folder')
        if path:
            self.path = path
            self.refresh()
            self.currentdir = path
        return

    def refresh(self):
        """Load files list into table"""

        ext = self.extensionvar.get()
        fp = '*.'+ext
        if self.recursivevar.get() == 1:
            fp = '**/*.csv'
            flist = glob.glob(os.path.join(self.path,fp), recursive=True)
        else:
            flist = glob.glob(os.path.join(self.path,fp))
        sizes = []
        cols=[]; rows=[]
        for f in flist:
            s = os.path.getsize(f)
            sizes.append(s)
            df = pd.read_csv(f, nrows=10)
            cols.append(len(df.columns))

        df = pd.DataFrame({'filename':flist, 'filesize':sizes,
                            'columns':cols})
        #print (df)
        self.pt.model.df = df
        self.pt.autoResizeColumns()
        self.pt.columnwidths['filename'] = 300
        #self.pt.redraw()
        return

    def loadFile(self, row=None):
        """Load a file from the table"""

        if row is None:
            row = self.pt.currentrow
        df = self.pt.model.df
        r = df.iloc[row]
        df = pd.read_csv(r.filename, sep=self.delimvar.get())
        idx=self.indexcolvar.get()
        df=df.set_index(df.columns[idx])
        return df

    def previewTable(self):
        """Preview selected table in main table."""

        df = self.loadFile()
        #print (df)
        table = self.parent.getCurrentTable()
        table.model.df = df
        table.autoResizeColumns()
        return

    def importAll(self):
        """Import selected or all files as tables"""

        ops = ['separately', 'join']
        d = dialogs.MultipleValDialog(title='Batch Import Files',
                                initialvalues=[ops],
                                labels=['How to Import:'],
                                types=['combobox'],
                                parent = self.mainwin)
        if d.result == None:
            return
        how = d.results[0]
        if how == 'join':
            self.joinTables()
        else:
            filelist = self.pt.model.df
            for i,r in filelist.iterrows():
                df = self.loadFile(i)
                self.parent.addSheet(i, df)
        return

    def joinTables(self):
        """Joins selected tables together and send to dataexplore"""

        filelist = self.pt.model.df
        res=[]
        for i,r in filelist.iterrows():
            df = self.loadFile(i)
            res.append(df)
        res = pd.concat(res)
        t = time.strftime('%X')
        self.parent.addSheet('joined-'+t, res)
        return

    def clear(self):
        """Clear file list"""

        self.path = None
        self.pt.model.df = pd.DataFrame()
        self.pt.redraw()
        return

    def previewPlot(self):
        """Make preview plot"""

        df = self.loadFile()
        self.pf.replot(df)
        return

    def batchPlot(self):
        """Plot multiple files"""

        plotdir = 'batchplots'
        df = self.pt.model.df
        for i,r in df.iterrows():
            f = r.filename
            name = os.path.basename(f)
            df = self.loadFile(i)
            if len(df)==0:
                continue
            self.pf.replot(df)
            self.pf.fig.suptitle(name)
            self.pf.savePlot(filename=os.path.join(plotdir, name+'.png'))

        return

    def test(self):
        path='test_batch'
        for i in range(20):
            df = TableModel.getSampleData()
            df.to_csv(os.path.join(path,'test%s.csv' %str(i)))
        return

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--dir", dest="directory",
                        help="Folder of raw files")

    opts, remainder = parser.parse_args()
    app = BatchProcessPlugin()
    if opts.directory != None:
        app.addFolder(opts.directory)
    app.mainloop()

if __name__ == '__main__':
    main()
