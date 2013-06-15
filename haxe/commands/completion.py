import haxe.completion.hx.constants as hxcc

import sublime_plugin
from haxe.log import log
from haxe.completion.hx.types import CompletionOptions
from haxe.completion.hx.base import trigger_completion

class HaxeAsyncTriggeredCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit) :

        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_ASYNC, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_REGULAR)
        trigger_completion(self.view, options)


class HaxeDisplayCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit, input_char = None) :
        log("RUN - HaxeDisplayCompletionCommand")
        if input_char != None:
            self.view.run_command("insert" , {
                "characters" : input_char
            })
        log("RUN - HaxeDisplayCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_REGULAR)
        trigger_completion(self.view, options)


class HaxeDisplayMacroCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("RUN - HaxeDisplayMacroCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_REGULAR)
        trigger_completion(self.view, options)
        
        

class HaxeHintDisplayCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("RUN - HaxeHintDisplayCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_HINT)
        trigger_completion(self.view, options)

class HaxeMacroHintDisplayCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("RUN - HaxeMacroHintDisplayCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_MACRO, 
            hxcc.COMPLETION_TYPE_HINT)
        trigger_completion(self.view, options)
   