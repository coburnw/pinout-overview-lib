import os
import sys
import json

from pinoutOverview import page as Page
from pinoutOverview import pinouts as Pinouts
from pinoutOverview import config as Config
from pinoutOverview import packages as Packages
from pinoutOverview import pins as Pins

from template import dxcore_page

class Variant():
    def __init__(self, name, data):
        self.variant_name = name
        self.data = data

        #print(self.data)
        pin_map=self.data['pin_map']
        
        self.pins = Pins.Pins(pin_map, self.get_pin_functions())
        self.package = Packages.PackageFactory(self.get_package_config(), self.pins.spacing)
        
        return

    def build_page(self, family_page_data):
        page_config = self.get_page_config(family_page_data)
        pinout = Pinouts.PinoutFactory(page_config['data']['layout'], self.pins, self.package)
        
        return Page.Page(page_config, pinout)
        
    def get_package_config(self):
        package_map = dict(spdip='sop', soic='sop', ssop='sop', tqfp='qfp', vqfn='qfn')
        shape, sep, count = self.data['package'].partition('-')
        if shape.lower in ['sop', 'qfp', 'qfn']:
            pin_count = int(count)
        elif shape.lower() in package_map:
            shape = package_map[shape.lower()]
            pin_count = int(count)
        else:
            print('unrecognized package shape: {}'.format(shape))
            raise
        
        package = dict(
            type = shape,
            pin_count = pin_count,
            text1 = self.data['part_range'],
            text2 = self.data['package_range']
        )
        
        return package

    def get_page_config(self, family_data):
        # sanity checks
        if 'layout' not in family_data:
            family_data['layout'] = 'orthogonal'

        if 'header' not in family_data:
            family_data['header'] = dict(
                text = '',
                subtext = ''
            )
            
        if 'footer' not in family_data:
            family_data['footer'] = dict(
                text = '',
                subtext = ''
            )
            
        if 'notes' not in family_data:
            family_data['notes'] = ['','','','']

        # merge variant data
        page_data = dict(family_data)
        
        if 'header' in self.data:
            page_data['header'] |= self.data['header']

        if 'footer' in self.data:
            page_data['footer'] |= self.data['footer']

        if 'notes' in self.data:
            for i, note in enumerate(self.data['notes']):
                if len(note) > 0:
                    page_data['notes'][i] = note

        page_data['quadrant'] = dict(
            text1 = page_data['notes'][0],
            text2 = page_data['notes'][1],
            text3 = page_data['notes'][2],
            text4 = page_data['notes'][3]
        )
            
        page_config = dict(
            template = dxcore_page.page_template,
            data = page_data
        )

        return page_config
    
    def get_pin_functions(self):
        family_functions = Config.FamilyFunctions()
        family_functions.styles = 'dxcore_functions'

        try:
            for pin_name, function_list in self.data['pins'].items():
                #print(pin_name)
                for key,values in function_list.items():
                    #print(' {} {}'.format(key,values))

                    # get function type and peripheral index
                    ftype = key.rstrip('0123456789').lower()
                    try:
                        index = int(key[len(ftype):])
                    except:
                        index = 0
                    
                    if ftype in ['tca','tcb','tcd']:
                        ftype = 'pwm'

                    if ftype in ['ac', 'ain', 'zcd']:
                        ftype = 'analog'

                    if ftype in ['usart', 'twi', 'spi', 'vrefa']:
                        ftype = 'serial'
                    
                    if ftype in ['ccl', 'evsys']:
                        ftype = 'logic'
                    
                    if ftype in ['pin', 'vddio', 'vdd', 'gnd']:
                        index = 0

                    for fname in values:
                        fname = str(fname)
                        #print(fname)

                        if index > 0:
                            fname = '{},{}'.format(index, fname)

                        is_alt = False
                        if 'ALT' in fname:
                            is_alt = True
                            fname = fname.replace('_ALT','')
                    
                        family_functions.append(pin_name, fname, ftype, is_alt)
        except:
            print('{}: failed to parse function list for pin {}'.format(self.variant_name, pin_name))
            raise
        
        return family_functions.functions


def load(name):
    section = 'atpack'

    basename = os.path.basename(name)
    name, suffix = os.path.splitext(basename)

    path = '{}/{}.json'.format(section,name)
    print('loading config file: {}'.format(path))

    with open(path, 'r') as fp:
        family = json.load(fp)
        
    return family
    

if __name__ == "__main__":

    entity_name = 'dxcore'
    Pinouts.entity(entity_name)

    family = load(sys.argv[1])
    page_data = family['page']
    
    for name, item in family.items():
        if name == 'page':
            continue

        print('processing variant {}'.format(name))
        variant = Variant(name, item)
        page = variant.build_page(page_data)

        print('saving to {}.svg'.format(name))
        page.save(name)
        

