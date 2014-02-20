#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import gtk

def responseToDialog(entry, dialog, response):
    dialog.response(response)

def getText(prompt, title=None , markup=None):
    #base this on a message dialog
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_QUESTION,
        gtk.BUTTONS_OK,
        None)
    if title:
        dialog.set_title(title)
    if markup:
        dialog.set_markup(markup)
    #create the text input field
    entry = gtk.Entry()
    #allow the user to press enter to do ok
    entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
    #create a horizontal box to pack the entry and a label
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label(prompt), False, 5, 5)
    hbox.pack_end(entry)
    #add it and show it
    dialog.vbox.pack_end(hbox, True, True, 0)
    dialog.show_all()
    #go go go
    dialog.run()
    text = entry.get_text()
    dialog.destroy()
    return text

def getChoice(prompt,choices,title=None, markup=None):
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_QUESTION,
        gtk.BUTTONS_OK,
        None)
    if title:
        dialog.set_title(title)
    if markup:
        dialog.set_markup(markup)
        
    vbox = gtk.VBox()
    vbox.pack_start(gtk.Label(prompt), False, 5, 5)    
    b1=gtk.RadioButton(label=str(choices[0]))
    b=[b1]
    vbox.add(b1)
    for i in range(1,len(choices)):
         b2 = gtk.RadioButton(label=str(choices[i]), group=b1)
         vbox.add(b2)
         b.append(b2)
    dialog.vbox.pack_end(vbox, True, True, 0)
    dialog.show_all()
    dialog.run()
    for i in b:
        if i.get_active():
            ret=i.get_label()
            dialog.destroy()
            return ret
