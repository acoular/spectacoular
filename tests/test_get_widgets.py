# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
#------------------------------------------------------------------------------

import unittest
import spectacoular as ac

class Test_Instancing(unittest.TestCase):
    """Test that ensures that classes can be instanciated and that get_widgets method
    can be called.
    """
    def test_instancing(self):
        """ test that all SpectAcoular classes can be instanciated """
        for i in dir(ac):
            with self.subTest(i):
                j = getattr(ac,i) # class, function or variable
                if isinstance(j,type): # is this a class ?
                    if hasattr(j,'get_widgets'):
                        #print(j)
                        j()

    def test_get_widgets(self):
        """ test that get_widgets can be called"""
        # iterate over all Acoular definitions labels
        for i in dir(ac):
            j = getattr(ac,i) # class, function or variable
            if isinstance(j,type): # is this a class ?
                if hasattr(j,'get_widgets') and hasattr(j,'trait_widget_mapper'):
                    #print(j)
                    j_instance = j()
                    # now test each default mapping individually
                    for key,value in j_instance.trait_widget_mapper.items():
                        with self.subTest(j.__name__ + ", " + key):
                            arg = j_instance.trait_widget_args.get(key)
                            if arg:
                                j_instance.get_widgets({key:value},{key:arg})
                            else:
                                j_instance.get_widgets({key:value})


if __name__ == '__main__':
    unittest.main()
