############
# Standard #
############

###############
# Third Party #
###############
import numpy as np
from bluesky import RunEngine
from bluesky.plans import outer_product_scan, scan
from bluesky.examples import Mover, Reader

##########
# Module #
##########
from pswalker.callbacks import apply_filters, LinearFit, MultiPitchFit

def test_linear_fit():
    #Create RunEngine
    RE = RunEngine()

    #Excepted values of fit
    expected = {'slope' : 5, 'intercept' : 2}

    #Create simulated devices
    motor = Mover('motor', {'motor' : lambda x : x}, {'x' :0})
    det   = Reader('det',
                   {'centroid' : lambda : 5*motor.read()['motor']['value'] + 2})

    #Assemble fitting callback
    cb = LinearFit('centroid', 'motor',
                    update_every=None)

    #Scan through variables
    RE(scan([det], motor, -1, 1, 50), cb)

    #Check accuracy of fit
    for k,v in expected.items():
        assert np.allclose(cb.result.values[k], v, atol=1e-6)

    #Check we create an accurate estimate
    print(cb.result.fit_report())
    assert np.allclose(cb.eval(10), 52, atol=1e-5)


def test_multi_fit():
    #Create RunEngine
    RE = RunEngine()

    #Excepted values of fit
    expected = {'x0' : 5, 'x1' : 4, 'x2' : 3}

    #Create simulated devices
    m1 = Mover('m1', {'m1' : lambda x : x}, {'x' :0})
    m2 = Mover('m2', {'m2' : lambda x : x}, {'x' :0})
    det   = Reader('det',
                   {'centroid' : lambda : 5 + 4*m1.read()['m1']['value']
                                          + 3*m2.read()['m2']['value']})

    #Assemble fitting callback
    cb = MultiPitchFit('centroid', ('m1','m2'),
                       update_every=None)

    #Scan through variables
    RE(outer_product_scan([det], m1, -1, 1, 10, m2, -1, 1, 10, False),
                          cb)
    #Check accuracy of fit
    print(cb.result.fit_report())
    for k,v in expected.items():
        assert np.allclose(cb.result.values[k], v, atol=1e-6)

    #Check we create an accurate estimate
    assert np.allclose(cb.eval(5,10), 55, atol=1e-5)


def test_apply_filters():
    mock_doc = {'data' : {'a' : 4,
                          'b' : -1}
               }
    #Passing filters
    assert apply_filters(mock_doc, filters={'a' : lambda x : x > 0}
            )
    #Block non-zero
    assert not apply_filters(mock_doc,  filters={'b' : lambda x : x > 0})

    #Exclude missing
    assert not apply_filters(mock_doc, filters={'c' : lambda x : True})
   
    #Exclude NaN
    mock_doc['c'] = np.nan
    assert not apply_filters(mock_doc, filters={'c' : lambda x : True})
    
    #Include missing
    assert apply_filters(mock_doc, filters={'c' : lambda x : True},
                             drop_missing=False)