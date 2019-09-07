'''
Provides windows for viewing and editing data arrays in tao
'''
import tkinter as tk
import ttk
from tkinter import messagebox
from tkinter import filedialog
from tao_widget import *
from parameters import str_to_tao_param, tao_parameter_dict
from tao_set import *
from tao_base_windows import *
from tao_lat_windows import tao_ele_browser
#-----------------------------------------------------
# d2_data window

class tao_d2_data_window(tao_list_window):

    def __init__(self, root, pipe, *args, **kwargs):
        self.tao_id = 'data'
        tao_list_window.__init__(self, root, "Data", *args, **kwargs)
        self.pipe = pipe
        univ_list = self.pipe.cmd_in("python super_universe")
        n_universe = str_to_tao_param(univ_list.splitlines()[0])
        self.univ_frame = tk.Frame(self)
        tk.Label(self.univ_frame, text="Universe: ").grid(row=0,column=0,sticky="E")
        self.u_ix = tk.StringVar()
        u_ix_list = []
        for i in range(n_universe.value):
            u_ix_list.append(str(i+1))
        self.u_ix.set(u_ix_list[0])
        u_ix_box = tk.OptionMenu(
                self.univ_frame, self.u_ix, *u_ix_list, command=self.refresh)
        u_ix_box.grid(row=0,column=1,sticky="W")
        self.univ_frame.pack(fill="both", expand=0)
        tk.Button(self, text='Write data to namelist file...',
                command=self.write_data).pack(side='left')

        # Populate self.list_frame
        self.refresh()


    def refresh(self):
        '''
        Clears self.list_frame and fills it with the current universe's
        d2/d1 data
        '''
        # Clear self.list_frame:
        for child in self.list_frame.winfo_children():
            child.destroy()
        # Get this universe's d2_data
        u_ix = self.u_ix.get()
        d2_data_list = self.pipe.cmd_in("python data_d2_array " + u_ix)
        d2_data_list = d2_data_list.splitlines()
        if len(d2_data_list) == 0:
            tk.Label(self.list_frame, text="NO DATA FOR THIS UNIVERSE").pack()
            messagebox.showwarning('Warning',
                    'No data are defined for universe ' + str(u_ix), parent=self)
            return
        for d2_data_item in d2_data_list:
            new_frame = d2_data_frame(
                    self.list_frame, self.root, self.pipe, d2_data_item, u_ix)
            new_frame.frame.pack()

    def write_data(self):
        '''
        Asks for a filename and writes the data to that file as a namelist
        '''
        out_file = filedialog.asksaveasfilename(title="Save namelist as...")
        if out_file != ():
            self.pipe.cmd_in('write namelist -data ' + out_file)


#-----------------------------------------------------
# d1_data window

class tao_d1_data_window(lw_table_window):
    '''
    With lw set to True, opens a lw_table_window instead
    '''
    def __init__(self, root, pipe, d1_data_name,
            u_ix, ix_lb, ix_ub, *args, **kwargs):
        self.tao_id = 'data'
        self.u_ix = u_ix
        self.ix_lb = ix_lb
        self.ix_ub = ix_ub
        self.lw = root.lw
        title_list = ["Index",
                "d1_data_name",
                "Merit type",
                "Ref Element",
                "Start Element",
                "Element Name",
                "Meas value",
                "Model value",
                "Design value",
                "Useit_opt",
                "Useit_plot",
                "good_user",
                "Weight",
                "Exists"]
        bulk_template = []
        bulk_template.append([str_to_tao_param("meas_value;REAL;T;"), 6])
        bulk_template.append([str_to_tao_param("good_user;LOGIC;T;"), 11])
        bulk_template.append([str_to_tao_param("weight;REAL;T;"), 12])

        bulk_set_format = "set data " + str(self.u_ix) + '@{}|'
        set_format = "set data " + str(self.u_ix) + '@{}[{}]|'
        self.set_exists = "set data " + str(self.u_ix) + '@' + d1_data_name + "|exists = T"
        if self.lw:
            lw_table_window.__init__(self, root, pipe, d1_data_name, title_list,
                    bulk_template, bulk_set_format, set_format, *args, **kwargs)
        else:
            table_window.__init__(self, root, pipe, d1_data_name, title_list,
                    bulk_template, bulk_set_format, set_format, *args, **kwargs)

    def refresh(self):
        self.d_list = self.pipe.cmd_in(
                "python data_d_array " + self.u_ix + '@' + self.array_name)
        self.d_list = self.d_list.splitlines()
        self.row_num = len(self.d_list)
        if self.lw:
            lw_table_window.refresh(self)
        else:
            table_window.refresh(self)

    def list_row_fetch(self, index):
        '''
        Returns row number index to be appended to self.list_rows
        '''
        return d1_data_list_entry(self.list_frame, self.d_list[index])

    def lw_list_row_fetch(self, index):
        '''
        For use with lw_table_window.  Returns a list of the values
        to be displayed in each column of row #index.
        '''
        return self.d_list[index].split(';')

    def lw_detail_callback(self, event=None):
        '''
        Callback for the light-weight table to open a detail window
        '''
        lw_table_window.open_detail_window_callback(self, event)

    def bulk_set(self, fill_choices, parent):
        '''
        Overload of lw_table_window.bulk_set that calls refresh data and plot windows
        '''
        lw_table_window.bulk_set(self, fill_choices, parent)
        # Refresh data-related windows
        for win in self.root.refresh_windows['data']:
            win.refresh()
        for win in self.root.refresh_windows['plot']:
            win.refresh()

    def open_detail_window(self, index):
        self.param_list = self.pipe.cmd_in("python data " + str(self.u_ix) + '@'
                + self.array_name + '[' + str(index) + ']')
        self.param_list = self.param_list.splitlines()
        for i in range(len(self.param_list)):
            self.param_list[i]=str_to_tao_param(self.param_list[i])
        if self.lw:
            lw_table_window.open_detail_window(self, index)
        else:
            table_window.open_detail_window(self, index)

    def detail_set_callback(self, tao_list, set_str):
        '''
        Overload of lw_table_window.detail_set_callback that refreshes
        data-related windows
        '''
        lw_table_window.detail_set_callback(self, tao_list, set_str)
        # Refresh data-related windows
        for win in self.root.refresh_windows['data']:
            win.refresh()
        for win in self.root.refresh_windows['plot']:
            win.refresh()

class tao_new_data_window(Tao_Toplevel):
    '''
    Provides a window for creating new d2 data arrays (and their associated
    d1 arrays)
    Pass the name of an existing d2_array to open that array and start editing its d1_arrays
    '''
    def __init__(self, root, pipe, default=None, *args, **kwargs):
        self.root = root
        Tao_Toplevel.__init__(self, root, *args, **kwargs)
        self.pipe = pipe
        self.rowconfigure(0, weight=1)
        self.title('New Data')
        self.name = ""

        #Frame for inputting d2 parameters
        self.d2_frame = tk.Frame(self)
        self.d2_frame.grid(row=0, column=0, sticky='NSEW')

        #Frames for inputting d1 parameters
        self.d1_frame = tk.Frame(self)
        self.nb_exists = False #used to track if the ttk Notebook has been set up
        self.d1_frame_list = []

        self.fill_d2_frame()
        if default != None:
            self.d2_param_list[0].tk_var.set(default)
            self.load_d1_frame(ask=False)
            for d1_frame in self.d1_frame_list:
                d1_frame.fill_defaults()

    def fill_d2_frame(self):
        tk.Label(self.d2_frame, text="New d2 Data",
                font=('Sans', 16, 'bold')).grid(
                        row=0, column=0, columnspan=2, sticky='EW')

        # Small bit of setup
        self.uni = tk.StringVar()
        self.uni.set("All")
        uni_max = self.pipe.cmd_in("python super universe")
        uni_max = str_to_tao_param(uni_max.splitlines()[0]).value
        uni_list = ["All"] + list(range(1, uni_max+1))
        def my_ttp(x):
            ''' shorcut for the following commonly used construct '''
            return tk_tao_parameter(str_to_tao_param(x), self.d2_frame, self.pipe)

        # Clone existing d2
        existing_d2_arrays = self.pipe.cmd_in("python data_d2_array 1")
        existing_d2_arrays = ['None'] + existing_d2_arrays.splitlines()
        self.clone_d2 = tk.StringVar()
        self.clone_d2.set('None')

        # Widgets
        self.d2_param_list = [my_ttp("name;STR;T;"),
                tk.OptionMenu(self.d2_frame, self.uni, *uni_list),
                my_ttp("data_source;ENUM;T;"),
                my_ttp("data^merit_type;ENUM;T;"),
                my_ttp("weight;REAL;T;"),
                my_ttp("good_user;LOGIC;T;T"),
                tk.OptionMenu(self.d2_frame, self.clone_d2, *existing_d2_arrays)]

        # Labels
        self.d2_label_list = [tk.Label(self.d2_frame, text="d2_data Name:"),
                tk.Label(self.d2_frame, text="Which universe:"),
                tk.Label(self.d2_frame, text="Default data source:"),
                tk.Label(self.d2_frame, text="Default merit type:"),
                tk.Label(self.d2_frame, text="Default weight:"),
                tk.Label(self.d2_frame, text="Default good_user:"),
                tk.Label(self.d2_frame, text="Clone existing d2_array:")]

        # Grid widgets and labels
        for i in range(len(self.d2_param_list)):
            self.d2_label_list[i].grid(row=i+1, column=0, sticky='W')
            if i in [1, 6]: #non tk_tao_parameters
                self.d2_param_list[i].grid(row=i+1, column=1, sticky='EW')
            else:
                self.d2_param_list[i].tk_wid.grid(row=i+1, column=1, sticky='EW')

        # Warning labels
        self.name_warning_1 = tk.Label(self.d2_frame, text="Cannot be empty")
        # Next button
        self.next_b = tk.Button(self.d2_frame, text="Next", command=self.load_d1_frame)
        self.next_b.grid(row=i+2, column=1, sticky='W')

        # Focus the name entry
        self.d2_param_list[0].tk_wid.focus_set()

    def load_d2_frame(self):
        self.d1_frame.pack_forget()
        self.d2_frame.grid(row=0, column=0, sticky='NSEW')

    def load_d1_frame(self, ask=True):
        '''
        Ungrids self.d2_frame, grids self.d1_frame, and sets up a notebook
        for the d1_frames if necessary.
        Set ask=False to skip message boxes
        '''
        clone_dict = {} # keys=d2_array names, values=lists of d1s
        # Check if d2_name is nonempty
        name = self.d2_param_list[0].tk_var.get().strip()
        if name == "":
            self.name_warning_1.grid(row=1, column=2, sticky='W')
            return

        # Conditions
        c1 = (name in self.pipe.cmd_in('python data_d2_array 1').splitlines()) #name in use
        c2 = (self.clone_d2.get() != 'None') #clone has been specified
        c3 = (self.name != name) #name has changed
        c4 = False #discard existing work
        ans_var = tk.StringVar()
        # Ask if user wants to keep existing data
        if c3 and self.name:
            self.name = name
            if ask:
                tao_message_box(self.root, self, ans_var, title='Warning', message='Would you like to keep or discard the d1_arrays you defined for ' + self.name + '?', choices=['Keep', 'Discard'])
            else:
                ans_var.set('Discard')
            if ans_var.get() == 'Keep':
                c4 = False
            elif ans_var.get() == 'Discard':
                c4 = True
            else:
                return
        # Ask if user wants to load existing data
        if c1:
            if ask:
                ans = messagebox.askyesno('Warning', name + " already exists as a d2 data array.    Would you like to clone its existing d1_arrays?", parent=self)
            else:
                ans = True
            if ans:
                # Will need to read in data for existing d2
                clone_dict[name] = self.pipe.cmd_in('python data_d1_array ' + name).splitlines()
        # Clone existing data
        if c2 and (self.clone_d2.get() != name):
            clone_dict[self.clone_d2.get()] = self.pipe.cmd_in('python data_d1_array ' + self.clone_d2.get()).splitlines()
        # Remake d1_frames and notebook if necessary
        if c4 and self.nb_exists:
            for frame in self.d1_frame_list:
                frame.destroy()
            self.d1_frame_list = []
            self.notebook.destroy()
            self.new_tab_frame.destroy()
            self.back_b.destroy()
            self.create_b.destroy()
            self.nb_exists = False
        else:
            self.name = name
            self.name_warning_1.grid_forget()

        # Possibly create self.notebook
        if not self.nb_exists:
            self.notebook = ttk.Notebook(self.d1_frame)
            self.notebook.pack(side='top', fill='both', expand=1)
            self.nb_exists = True

            self.d1_index = 0 #marks current tab index

            # New tab button
            self.new_tab_frame = tk.Frame(self.notebook)
            self.notebook.insert('end', self.new_tab_frame)
            self.notebook.tab(len(self.d1_frame_list), text='+')
            self.notebook.bind('<<NotebookTabChanged>>', self.tab_handler)

            # Back button
            self.back_b = tk.Button(self.d1_frame, text="Back", command=self.load_d2_frame)
            self.back_b.pack(side='left')

            # Create button
            self.create_b = tk.Button(self.d1_frame, text="Create!", command=self.create_data)
            self.create_b.pack(side='right')

        self.d2_frame.grid_forget()
        self.d1_frame.pack(fill='both', expand=1)
        self.title("New data: " + self.d2_param_list[0].tk_var.get())

        # Clone the requested d2 array(s)
        if clone_dict != {}:
            # Progress window
            num_bars = 0
            for k in clone_dict.keys():
                num_bars += len(clone_dict[k])
            self.pw = tao_progress_window(self.root, self, num_bars)
            self.pw.title("Loading...")
            tk.Label(self.pw, text='Loading existing d1_arrays').grid(row=0, column=0, columnspan=2, sticky='EW')
            # Find correct universe number
            if self.uni.get() == "All":
                u = "1"
            else:
                u = self.uni.get()
            if name in clone_dict.keys():
                for d1 in clone_dict[name]:
                    self.add_d1_frame(d1, u+'@'+name)
            if (self.clone_d2.get() in clone_dict.keys()) and (name != self.clone_d2.get()):
                for d1 in clone_dict[self.clone_d2.get()]:
                    self.add_d1_frame(d1, u+'@'+self.clone_d2.get())
            self.notebook.select(0)
            self.pw.destroy()

        # Copy d2 defaults into d1_arrays
        for i in range(len(self.d1_frame_list)):
            val = self.d2_param_list[2].tk_var.get()
            self.d1_frame_list[i].d1_array_wids[1].tk_var.set(val)
            val = self.d2_param_list[3].tk_var.get()
            self.d1_frame_list[i].d1_array_wids[3].tk_var.set(val)
            val = self.d2_param_list[4].tk_var.get()
            self.d1_frame_list[i].d1_array_wids[4].tk_var.set(val)

    def create_data(self, event=None):
        '''
        Takes the information from the d2_frame and d1_frames and runs
        the necessary commands to create the data in tao, then closes
        the create data window
        '''
        # Input validation
        messages = []
        for d1_frame in self.d1_frame_list:
            # Check names
            if d1_frame.name_handler():
                name_m = "Please check d1_array names."
                if name_m not in messages:
                    messages.append(name_m)
            if d1_frame.ix_min_handler():
                messages.append("Please check the start index for " + d1_frame.name)
            if d1_frame.ix_max_handler():
                messages.append("Please check the end index for " + d1_frame.name)
            if d1_frame.d1_array_wids[2].tk_var.get() == "":
                messages.append("Please choose a data type for " + d1_frame.name)
            # Check for semicolons in any fields
            semi_message = "Semicolons not allowed in any input field"
            caret_message = "Carets not allowed in any input field"
            broken = False #Used to break out of the below for loops
            # Check for semicolons/carets
            for ttp in d1_frame.d1_array_wids:
                if str(ttp.tk_var.get()).find(';') != -1:
                    messages.append(semi_message)
                    broken = True
                    break
                if str(ttp.tk_var.get()).find('^') != -1:
                    messages.append(caret_message)
                    broken = True
                    break
            for data_dict in d1_frame.data_dict.values():
                if broken:
                    break
                for d in data_dict.values():
                    if str(d).find(';') != -1:
                        messages.append(semi_message)
                        broken = True
                        break
                    if str(d).find('^') != -1:
                        messages.append(caret_message)
                        broken = True
                        break
                if broken:
                    break
        for m in messages:
            messagebox.showwarning("Error", m, parent=self)
        if messages != []:
            return
        # Book-keeping
        datum_params = ['data_type', 'ele_ref_name', 'ele_start_name', 'ele_name',
                'data^merit_type', 'meas_value', 'ref_value', 'weight', 'good_user',
                'data_source', 'eval_point', 's_offset', '1^ix_bunch',
                'invalid_value', 'spin_n0_x', 'spin_n0_y', 'spin_n0_z']
        d1_params = ['name', 'data_source', 'data_type', 'data^merit_type',
                'weight', 'good_user']
        d2_params = ['name', 'uni', 'data_source', 'data^merit_type', 'weight', 'good_user']
        # Create the data array
        if self.uni.get() == 'All':
            uni_max = self.pipe.cmd_in("python super universe")
            uni_max = str_to_tao_param(uni_max.splitlines()[0]).value
            uni_list = list(range(1, uni_max+1))
        else:
            uni_list = [int(self.uni.get())]
        d1_count = 0 # used to make the corrent number of progress bars
        for u in uni_list:
            cmd_str = 'python data_d2_create ' + str(u) + '@' + self.name
            cmd_str += '^^' + str(len(self.d1_frame_list)) + '^^'
            for d1_frame in self.d1_frame_list:
                d1_count += 1
                # min/max indices for each d1_array
                cmd_str += str(d1_frame.name) + '^^'
                cmd_str += str(d1_frame.ix_min) + '^^'
                cmd_str += str(d1_frame.ix_max) + '^^'
            # Create the d2/d1_arrays
            self.pipe.cmd_in(cmd_str)
        # Progress bars
        self.pw = tao_progress_window(self.root, self, d1_count)
        for u in uni_list:
            # Progress window config
            for d1_frame in self.d1_frame_list:
                self.pw.label_vars[self.pw.ix].set(
                        'Creating' + str(u) + '@' + self.name + '.' + d1_frame.name)
                self.pw.set_max(self.pw.ix, d1_frame.ix_max-d1_frame.ix_min+1)
                # set individual data parameters
                for j in range(d1_frame.ix_min, d1_frame.ix_max+1):
                    self.pw.set_val(self.pw.ix, j-d1_frame.ix_min)
                    cmd_str = 'python datum_create '
                    cmd_str += str(u) + '@' + self.name + '.' + d1_frame.name + '[' + str(j) + ']'
                    for p in datum_params:
                        #look in d1_frame.data_dict
                        if (j in d1_frame.data_dict.keys()) and (p in d1_frame.data_dict[j].keys()):
                            value = d1_frame.data_dict[j][p]
                        elif p in d1_params:
                            value = d1_frame.d1_array_wids[d1_params.index(p)].tk_var.get()
                        elif p in d2_params:
                            value = self.d2_param_list[d2_params.index(p)].tk_var.get()
                        else:
                            value = ""
                        if p == "good_user": # replace with T or F
                            value = "T" if value else "F"
                        cmd_str += '^^' + value
                    self.pipe.cmd_in(cmd_str)
                self.pw.ix += 1
        # Close the window
        self.destroy()
        # Refresh data-related windows
        for win in self.root.refresh_windows['data']:
            win.refresh()
        for win in self.root.refresh_windows['plot']:
            win.refresh()

    def tab_handler(self, event=None):
        '''
        Handles new tab creation and updates self.d1_index as necessary
        '''
        # Check if the new tab frame has been selected
        if self.notebook.select() == self.new_tab_frame._w:
            # Add new tab
            self.d1_frame_list.append(new_d1_frame(self))
            self.d1_index = len(self.d1_frame_list)-1
            self.notebook.insert(self.d1_index, self.d1_frame_list[-1])
            self.notebook.tab(self.d1_index, text='New d1_array')
            self.notebook.select(self.d1_index)
        else:
            # Update self.d1_index
            for i in range(len(self.d1_frame_list)):
                frame = self.d1_frame_list[i]
                if self.notebook.select() == frame._w:
                    self.d1_index = i
                    # Unblock frame's handlers
                    frame.handler_block = False
                    break

    def add_d1_frame(self, d1_name, d2_name, event=None):
        '''
        Creates a new d1_frame for d1_name and reads existing data in from Tao if present
        Takes a line of output from python data_d1_array for d1_name
        d2_name should be "uni@d2_name"
        '''
        d1 = d1_name.split(';')[3]
        self.d1_frame_list.append(
                new_d1_frame(self, name=d1, full_name=d2_name + '.' + d1))
        ix = len(self.d1_frame_list) - 1
        self.notebook.insert(ix, self.d1_frame_list[-1])
        self.notebook.tab(ix, text=d1)

    def refresh(self):
        '''
        Only here in case something tries to refresh this window
        '''
        pass

class new_d1_frame(tk.Frame):
    '''
    Provides a frame for inputting properties of a d1_data array.
    To load an existing d1_array, pass the d1_array name as name
    (e.g. x,y, NOT orbit.x, orbit.y)
    Also pass the full name that should be used for data lookup
    (e.g. 1@orbit.x)
    '''
    def __init__(self, d2_array, name="", full_name=""):
        tk.Frame.__init__(self, d2_array.notebook)
        self.d2_array = d2_array
        self.pipe = self.d2_array.pipe
        self.handler_block = False
        if name == "":
            self.name = "New d1_array" #Default
        else:
            self.name = name

        # d1 Widgets
        def d1_ttp(x):
            ''' Shortcut for commonly used construct '''
            return tk_tao_parameter(str_to_tao_param(x), self, self.pipe)

        self.d1_array_wids = [d1_ttp('name;STR;T;'),
                d1_ttp('data_source;ENUM;T;'),
                d1_ttp('data_type;DAT_TYPE;T;'),
                d1_ttp('data^merit_type;ENUM;T;'),
                d1_ttp('weight;REAL;T;'),
                d1_ttp('good_user;LOGIC;T;T'),
                d1_ttp('ix_min;INT;T;'),
                d1_ttp('ix_max;INT;T;')]
        # d1 labels (NAMES AS STRINGS ONLY)
        self.d1_array_labels = ["d1_array Name:", "Default data source:",
                "Default data type:", "Default merit type:", "Default weight",
                "Default good_user:", "Start index", "End index"]
        # Read in defaults from d2 level
        val = self.d2_array.d2_param_list[2].tk_var.get()
        self.d1_array_wids[1].tk_var.set(val)
        val = self.d2_array.d2_param_list[3].tk_var.get()
        self.d1_array_wids[3].tk_var.set(val)
        val = self.d2_array.d2_param_list[4].tk_var.get()
        self.d1_array_wids[4].tk_var.set(val)
        val = self.d2_array.d2_param_list[5].tk_var.get()
        self.d1_array_wids[5].tk_var.set(val)
        # Grid widgets and labels:
        for i in range(len(self.d1_array_wids)):
            tk.Label(self, text=self.d1_array_labels[i]).grid(row=i+2, column=0, sticky='W')
            self.d1_array_wids[i].tk_wid.grid(row=i+2, column=1, sticky='EW')
        i = i+2
        # Set name
        if self.name != "New d1_array":
            self.d1_array_wids[0].tk_var.set(self.name)

        # Warning labels
        # (defined here to be gridded/ungridded as necessary)
        self.name_warning_1 = tk.Label(self, text="Must not be empty")
        self.name_warning_2 = tk.Label(self, text="d1 name already in use")
        self.ix_min_warning_1 = tk.Label(self, text="Must be a non-negative integer")
        self.ix_min_warning_2 = tk.Label(self, text="Cannot be larger than the maximum index")
        self.ix_max_warning_1 = tk.Label(self, text="Must be a non-negative integer")
        self.ix_max_warning_2 = tk.Label(self, text="Cannot be smaller than the minimum index")

        # Responses to edits
        self.d1_array_wids[0].tk_wid.bind('<FocusOut>', self.name_handler)
        self.d1_array_wids[6].tk_wid.bind('<FocusOut>', self.ix_min_handler)
        self.d1_array_wids[7].tk_wid.bind('<FocusOut>', self.ix_max_handler)
        self.d1_array_wids[1].tk_var.trace('w', self.data_source_handler)
        self.d1_array_wids[2].tk_var.trace('w', self.data_type_handler)


        # "Fill" to datums
        def datum_fill_callback(ix):
            '''Helper function for buttons below'''
            return lambda : self.datum_fill(ix)
        for ix in range(1, 6):
            tk.Button(self, text="Fill to datums", command=datum_fill_callback(ix)).grid(row=ix+2, column=2)

        ttk.Separator(self, orient='horizontal').grid(row=i+1, column=0, columnspan=3, sticky='EW')
        i = i+1

        # Element browsers
        tk.Label(self, text="Choose elements:").grid(row=i+1, column=0, sticky='W')
        self.ele_name_button = tk.Button(self, text="Browse...",
                command=lambda : self.lat_browser('name'))
        self.ele_name_button.grid(row=i+1, column=1, sticky='EW')

        tk.Label(self, text="Start elements:").grid(row=i+2, column=0, sticky='W')
        self.ele_start_name_button = tk.Button(self, text="Browse...",
                command=lambda : self.lat_browser('start_name'))
        self.ele_start_name_button.grid(row=i+2, column=1, sticky='EW')

        tk.Label(self, text="Ref elements:").grid(row=i+3, column=0, sticky='W')
        self.ele_ref_name_button = tk.Button(self, text="Browse...",
                command=lambda : self.lat_browser('ref_name'))
        self.ele_ref_name_button.grid(row=i+3, column=1, sticky='EW')

        ttk.Separator(self, orient='horizontal').grid(row=i+4, column=0, columnspan=3, sticky='EW')
        i = i+1

        # Individual data
        self.data_dict = {}
        self.datum_frame = tk.Frame(self)
        tk.Label(self, text="Datum:").grid(row=i+4, column=0, sticky='W')
        self.data_ix = tk.StringVar()
        self.ix_min = -1
        self.ix_max = -1
        self.data_chooser = ttk.Combobox(self, textvariable=self.data_ix,
                values=['PLEASE SPECIFY MIN/MAX INDICES'], state='readonly')
        self.data_chooser.bind('<<ComboboxSelected>>', self.make_datum_frame)
        self.data_chooser.grid(row=i+4, column=1, sticky='EW')
        # Set ix_min and ix_max for existing d1_arrays
        if self.name != "New d1_array":
            ix_data = self.pipe.cmd_in('python data_d1_array ' + full_name)
            ix_data = ix_data.splitlines()
            for line in ix_data:
                if line.split(';')[3] == self.name:
                    break
            #line is now set to the relevant line
            self.d1_array_wids[-2].tk_var.set(line.split(';')[5])
            self.d1_array_wids[-1].tk_var.set(line.split(';')[6])
            self.ix_min_handler()
            self.ix_max_handler()
        # Fill self.data_dict for existing d1 arrays
        data_dict_params = ['data_source', 'data_type', 'ele_name', 'ele_start_name', 'ele_ref_name',
                'data^merit_type', 'meas_value', 'ref_value', 'weight', 'good_user', '1^ix_bunch',
                'eval_point', 's_offset']
        if self.name != "New d1_array":
            self.d2_array.pw.label_vars[self.d2_array.pw.ix].set(
                    'Loading ' + self.d2_array.name + '.' + self.name + '...')
            self.d2_array.pw.set_max(self.d2_array.pw.ix, self.ix_max-self.ix_min+1)
            #self.d2_array.update_idletasks()
            for i in range(self.ix_min, self.ix_max+1):
                self.d2_array.pw.set_val(self.d2_array.pw.ix, i-self.ix_min)
                #self.d2_array.update_idletasks()
                self.data_dict[i] = {}
                existing_data = self.pipe.cmd_in(
                        'python data ' + full_name + '[' + str(i) + ']')
                existing_data = existing_data.splitlines()
                for p in data_dict_params:
                    # Find correct line
                    for line in existing_data:
                        if line.find(p + ';') == 0:
                            break
                    # Write to self.data_dict
                    self.data_dict[i][p] = line.split(';')[3].strip()
            self.d2_array.pw.ix += 1
            # Load first datum
            self.data_ix.set(self.ix_min)
            self.make_datum_frame()

        # Delete button
        tk.Button(self, text="DELETE THIS D1_ARRAY", fg='red', command=self.delete).grid(
                row=0, column=0, columnspan=3, sticky='EW')

        # Duplicate button
        tk.Button(self, text="Duplicate this d1_array", command=self.duplicate).grid(
                row=1, column=0, columnspan=3, sticky='EW')

        # Focus the d1 name widget
        self.d1_array_wids[0].tk_wid.focus_set()

    def fill_defaults(self, event=None):
        '''
        Copies the properties of the first datum and makes them the defaults at the d1 level
        '''
        self.d1_array_wids[1].tk_var.set(self.data_dict[self.ix_min]['data_source'])
        self.d1_array_wids[2].tk_var.set(self.data_dict[self.ix_min]['data_type'])
        self.d1_array_wids[3].tk_var.set(self.data_dict[self.ix_min]['data^merit_type'])
        self.d1_array_wids[4].tk_var.set(self.data_dict[self.ix_min]['weight'])
        self.d1_array_wids[5].tk_var.set(True if self.data_dict[self.ix_min]['good_user'] == 'T' else False)

    def delete(self, ask=True, event=None):
        '''
        Deletes this d1_array frame
        Call with ask = False to skip confirmation
        '''
        # Ask for confirmation
        if ask:
            ans = messagebox.askokcancel("Delete " + self.name, "Delete this d1_array and its associated data?", parent=self.d2_array)
            if not ans:
                return

        # Remove from parent d1_frame_list
        ix = self.d2_array.d1_index
        if ix > 0:
            # Prefer to move to the tab to the left
            self.d2_array.notebook.select(ix-1)
        self.d2_array.d1_frame_list.pop(ix)

        # Destroy self
        self.destroy()

    def duplicate(self, event=None):
        '''
        Adds a new d1_frame to self.d2_array.d1_frame_list that is a copy of
        this frame, and changes focus to that frame
        '''
        # Don't run any handlers for this d1_frame
        self.handler_block = True
        self.d2_array.d1_frame_list.append(new_d1_frame(self.d2_array))
        ix = len(self.d2_array.d1_frame_list) - 1
        #self.d2_array.d1_index = ix
        # Copy properties into new frame
        self.d2_array.d1_frame_list[-1].name = self.name + '_copy'
        self.d2_array.d1_frame_list[-1].ix_min = self.ix_min
        self.d2_array.d1_frame_list[-1].ix_max = self.ix_max
        self.d2_array.d1_frame_list[-1].data_dict = self.data_dict
        for i in range(len(self.d1_array_wids)):
            if i == 0:
                self.d2_array.d1_frame_list[-1].d1_array_wids[i].tk_var.set(self.d1_array_wids[i].tk_var.get() + '_copy')
            else:
                self.d2_array.d1_frame_list[-1].d1_array_wids[i].tk_var.set(self.d1_array_wids[i].tk_var.get())
        # Run all input validation handlers
        self.d2_array.notebook.insert(ix, self.d2_array.d1_frame_list[-1])
        self.d2_array.notebook.select(ix)
        self.d2_array.tab_handler()
        self.update_idletasks()
        self.d2_array.d1_frame_list[-1].name_handler()
        self.d2_array.d1_frame_list[-1].ix_min_handler()
        self.d2_array.d1_frame_list[-1].ix_max_handler()
        self.d2_array.d1_frame_list[-1].data_source_handler()
        self.d2_array.d1_frame_list[-1].data_type_handler()

    def make_datum_frame(self, event=None):
        '''
        Adds an entry to self.data_dict if necessary, and updates
        self.datum_frame to show the values for the current datum
        '''
        ix = self.data_ix.get()
        if ix == 'PLEASE SPECIFY MIN/MAX INDICES':
            return
        ix = int(ix)
        if ix not in self.data_dict.keys():
            self.data_dict[ix] = {}
        self.datum_frame.destroy()
        self.datum_frame = tk.Frame(self)
        def datum_ttp(x):
            ''' Shortcut for commonly used construct '''
            return tk_tao_parameter(x, self.datum_frame, self.pipe)
        # Parameters
        param_list = ['data_source;ENUM;T;', 'data_type;DAT_TYPE;T;',
                'ele_name;STR;T;', 'ele_start_name;STR;T;', 'ele_ref_name;STR;T;',
                'data^merit_type;ENUM;T;', 'meas_value;REAL;T;', 'ref_value;REAL;T;',
                'weight;REAL;T;', 'good_user;LOGIC;T;T', '1^ix_bunch;INUM;T;',
                'eval_point;ENUM;T;', 's_offset;REAL;T;']
        param_list = list(map(str_to_tao_param, param_list))
        # Fill in defaults set at d1 level
        param_list[0].value = self.d1_array_wids[1].tk_var.get()
        param_list[1].value = self.d1_array_wids[2].tk_var.get()
        param_list[5].value = self.d1_array_wids[3].tk_var.get()
        param_list[8].value = self.d1_array_wids[4].tk_var.get()
        param_list[9].value = bool(self.d1_array_wids[5].tk_var.get())
        # Set parameter values if specified
        for i in range(len(param_list)):
            if param_list[i].name in self.data_dict[ix].keys():
                param_list[i].value = self.data_dict[ix][param_list[i].name]
        # Create widgets
        self.datum_wid_list = list(map(datum_ttp, param_list))
        def data_writer(i):
            ''' Writes the contents of self.datum_wid_list[i] into self.data_dict '''
            if self.datum_wid_list[i].param.type == 'LOGIC':
                val = bool(self.datum_wid_list[i].tk_var.get())
            else:
                val = self.datum_wid_list[i].tk_var.get()
            self.data_dict[ix][self.datum_wid_list[i].param.name] = val
        def data_writer_callback(i):
            ''' Callback for data_writer() '''
            return lambda *args : data_writer(i)

        # Set state of ele_names and s_offset for selected data_type
        def data_type_callback(*args):
            # ele_names
            if self.datum_wid_list[1]._has_ele():
                for i in range(2, 5):
                    self.datum_wid_list[i].tk_wid.configure(state='normal')
            else:
                for i in range(2, 5):
                    self.datum_wid_list[i].tk_wid.configure(state='disabled')
            # s_offset
            if self.datum_wid_list[1]._has_s_offset():
                self.datum_wid_list[11].tk_wid.configure(state='normal')
            else:
                self.datum_wid_list[11].tk_wid.configure(state='disabled')
        # Grid widgets
        for i in range(len(self.datum_wid_list)):
            self.datum_wid_list[i].tk_label.grid(row=i, column=0, sticky='E')
            self.datum_wid_list[i].tk_wid.grid(row=i, column=1, sticky='EW')
            # Write changes into self.data_dict
            self.datum_wid_list[i].tk_var.trace('w', data_writer_callback(i))
        self.datum_wid_list[1].tk_var.trace('w', data_type_callback)
        self.datum_frame.grid(row=20, column=0, columnspan=3, sticky='EW')

    def datum_fill(self, ix):
        '''
        "Fills" the value in self.d1_array_wids[ix] to all datums in self.data_dict
        Actually just erases the values in self.data_dict, which produces the same effect
        '''
        for i in self.data_dict.keys():
            param = self.d1_array_wids[ix].param.name
            if param in self.data_dict[i].keys():
                self.data_dict[i].pop(param)
            elif 'data^'+param in self.data_dict[i].keys():
                self.data_dict[i].pop('data^'+param)
        # Redraw datum frame to reflect changes
        try:
            int(self.data_ix.get())
            self.make_datum_frame()
        except ValueError:
            pass

    def lat_browser(self, which):
        '''
        Opens a modified lattice table window to select elements en masse
        which should be either 'name', 'start_name', or 'ref_name'
        When the elements are chosen, ele_which will be set for each of this
        d1_array's data sequentially
        '''
        # Make sure the name, ix_min, and ix_max are set
        if (bool(self.name_handler()) | bool(self.ix_min_handler())
                | bool(self.ix_max_handler())):
            return
        #
        name = self.d2_array.name + '.' + self.name
        win = tao_ele_browser(self.d2_array.root, self.pipe, name, self,
                'data', which, self.d2_array.uni.get())

    def name_handler(self, event=None):
        '''
        Changes the tab name to match the d1_name
        Returns 1 if unsuccessful
        '''
        if self.handler_block:
            return
        name = self.d1_array_wids[0].tk_var.get().strip()
        if name != "":
            # Make sure the name isn't already in use
            i = 0
            for d1 in self.d2_array.d1_frame_list:
                if (d1.name == name) & (self != self.d2_array.d1_frame_list[i]):
                    self.name_warning_1.grid_forget()
                    self.name_warning_2.grid(row=2, column=2, sticky='W')
                    return 1
                i = i+1

            self.d2_array.notebook.tab(self.d2_array.d1_index, text=self.name)
            self.name_warning_1.grid_forget()
            self.name_warning_2.grid_forget()
            if self.name != name:
                if self.d1_array_wids[2]._is_valid_dat_type(self.d2_array.name + '.' + name):
                    # set data type
                    self.d1_array_wids[2].tk_var.set(self.d2_array.name + '.' + name)
            self.name = name
        else:
            self.name_warning_2.grid_forget()
            self.name_warning_1.grid(row=2, column=2, sticky='W')
            self.name = "New d1_array"
            self.d2_array.notebook.tab(self.d2_array.d1_index, text="New d1_array")
            return 1

    def ix_min_handler(self, event=None):
        if self.handler_block:
            return
        try:
            ix_min = int(self.d1_array_wids[6].tk_var.get())
        except ValueError:
            ix_min = -1
        if ix_min > -1:
            self.ix_min = ix_min
            if (ix_min <= self.ix_max) | (self.ix_max == -1):
                self.ix_min_warning_1.grid_forget()
                self.ix_min_warning_2.grid_forget()
            else:
                self.ix_min_warning_1.grid_forget()
                self.ix_min_warning_2.grid(row=8, column=2, sticky='W')
                return 1
        else:
            self.ix_min_warning_2.grid_forget()
            self.ix_min_warning_1.grid(row=8, column=2, sticky='W')
            return 1
        # Update the data index range if possible
        if (self.ix_min > -1) & (self.ix_max >= self.ix_min):
            self.data_chooser.configure(values=list(range(self.ix_min, self.ix_max+1)))

    def ix_max_handler(self, event=None):
        if self.handler_block:
            return
        try:
            ix_max = int(self.d1_array_wids[7].tk_var.get())
        except ValueError:
            ix_max = -1
        if ix_max > -1:
            self.ix_max = ix_max
            if ix_max >= self.ix_min:
                self.ix_max_warning_1.grid_forget()
                self.ix_max_warning_2.grid_forget()
            else:
                self.ix_max_warning_1.grid_forget()
                self.ix_max_warning_2.grid(row=9, column=2, sticky='W')
                return 1
        else:
            self.ix_max_warning_2.grid_forget()
            self.ix_max_warning_1.grid(row=9, column=2, sticky='W')
            return 1
        # Update the data index range if possible
        if (self.ix_min > -1) & (self.ix_max >= self.ix_min):
            self.data_chooser.configure(values=list(range(self.ix_min, self.ix_max+1)))

    def data_source_handler(self, *args):
        '''
        Updates the data_source widget to only show valid data types
        for the currently selected data source
        '''
        if self.handler_block:
            return
        source = self.d1_array_wids[1].tk_var.get()
        if source in ['beam', 'lat']:
            # Remake self.d1_array_wids[2] (data type)
            old_val = self.d1_array_wids[2].tk_var.get()
            self.d1_array_wids[2].tk_wid.grid_forget()
            self.d1_array_wids[2] = tk_tao_parameter(
                    str_to_tao_param('data_type;DAT_TYPE;T;'),
                    self, self.pipe, data_source=source)
            self.d1_array_wids[2].tk_var.set(old_val)
            self.d1_array_wids[2].tk_var.trace('w', self.data_type_handler)
            self.d1_array_wids[2].tk_wid.grid(row=4, column=1, sticky='EW')

    def data_type_handler(self, *args):
        '''
        Sets the state of the ele buttons appropriately for the currently selected data type
        '''
        if self.handler_block:
            return
        if not self.d1_array_wids[2]._has_ele():
            self.ele_name_button.configure(state='disabled')
            self.ele_start_name_button.configure(state='disabled')
            self.ele_ref_name_button.configure(state='disabled')
        else:
            self.ele_name_button.configure(state='normal')
            self.ele_start_name_button.configure(state='normal')
            self.ele_ref_name_button.configure(state='normal')
