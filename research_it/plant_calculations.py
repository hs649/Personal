from aide_design.shared.units import unit_registry as u
import numpy as np
import pandas as pd

# pump rotor radius based on minimizing error between predicted and measured
# values
R_pump = 1.62 * u.cm

# empirically derived correction factor due to the fact that larger diameter
# tubing has more loss due to space smashed by rollers
k_nonlinear = 13

# maximum and minimum rpms for a 100 rpm pump
min_rpm = 3 * u.rev/u.min
max_rpm = 95 * u.rev/u.min


def ID_colored_tube(color):
    """This function looks up the inner diameter (ID) of a Masterflex 3-stop
    tube given the color of its tags.

    :param color : string
        color of the tubing to be used
    :return float:
        diameter of the tubing (mm)

    Examples
    --------
    >>> ID_colored_tube("yellow-blue")
    1.52 millimeter
    >>> ID_colored_tube("orange-yellow")
    0.51 millimeter
    >>> ID_colored_tube("purple-white")
    2.79 millimeter
    """
    df = pd.read_csv("tubing_data.txt", delimiter='\t')
    idx = df["Color"] == color
    return df[idx]['Diameter (mm)'].values[0] * u.mm


def volPerRev_small(color):
    """This function calculates the volume per revolution of a 6 roller pump
    given the tag colors of the Masterflex 3-stop tubing being used.
    The calculation was empirically derived using the table found at
    http://www.ismatec.com/int_e/pumps/t_mini_s_ms_ca/tubing_msca2.htm
    Parameters
    ----------
    color : string
        color of the tubing to be used
    Returns
    -------
    float
        flow from the 6 roller pump (mL/rev)
    Examples
    --------

    ////////////TODO : change inputs to colors///////////////

    >>> volPerRev_small(2.79*u.mm)
    0.4005495805189351 milliliter/rev
    >>> volPerRev_small(1.52*u.mm)
    0.14884596727278446 milliliter/rev
    >>> volPerRev_small(0.51*u.mm)
    0.01943899117521222 milliliter/rev
    """
    inner_diameter = ID_colored_tube(color)
    distance = (R_pump * 2 * np.pi - k_nonlinear * inner_diameter) / u.rev
    area = np.pi * (inner_diameter/2) ** 2
    return (distance * area).to(u.mL/u.rev)


def pump_flow(vol_per_rev, rpm):
    return (vol_per_rev * rpm).to(u.mL/u.s)


def pump_rpm(vol_per_rev, flow_rate):
    return (flow_rate / vol_per_rev).to(u.rev/u.min)


def C_stock(Q_plant, C_plant, pump_flow):
    """This function calculates the stock concentration of a generic
    material given desired concentration in the plant.
    Parameters
    ----------
    Q_plant : float
        flow rate of the plant
    C : float
        desired concentration of the material within the plant
    tubing_color : string
        color of the tubing to be used
    Returns
    -------
    float
        maximum stock concentration (g/L)
    Examples
    --------
    >>> C_stock_max(7*u.mL/u.s, 100*u.NTU, "yellow-blue")
    159.89684125188708 gram/liter
    >>> C_stock_max(7*u.mL/u.s, 2*u.mg/u.L, "orange-yellow")
    14.404039668326215 gram/liter
    """
    return (Q_plant * C_plant / pump_flow).to(u.mg/u.L)


def dilution_factor(C_stock, C_super_stock):
    '''
    Parameters
    ----------
    C_stock : float
        concentration of the stock solution connected to the pump
    C_super_stock : float
        concentration of the super stock solution from which stock is made
    '''
    return (C_stock / C_super_stock).to(u.mL/u.L)


def Q_stock(Q_plant, C_plant, C_stock):
    """This function calculates the flow rate of the stock of the desired
    concentration.
    Parameters
    ----------
    Q_plant : float
        flow rate of the plant
    C : float
        desired concentration within the plant
    tubing_color : string
        color of the tubing to be used
    Returns
    -------
    float
        flow rate of the stock (mL/s)
    Examples
    --------
    >>> Q_stock_max(7*u.mL/u.s, 100*u.NTU, "yellow-blue")
    0.007442298363639224 milliliter/second
    >>> Q_stock_max(7*u.mL/u.s, 2*u.mg/u.L, "orange-yellow")
    0.0009719495587606109 milliliter/second
    """
    return (Q_plant * C_plant / C_stock).to(u.mL/u.s)


def T_stock(Q_plant, C, tubing_color, V_stock):
    """This function calculates the time after the experiment at which the
    stock container will run out.
    Parameters
    ----------
    Q_plant : float
        flow rate of the plant
    C : float
        desired concentration within the plant
    tubing_color : string
        color of the tubing to be used
    V_stock : float
        volume of the stock container
    Returns
    -------
    float
        time before the stock is depleted (hr)
    Examples
    --------
    >>> T_stock(7*u.mL/u.s, 100*u.NTU, "yellow-blue", 1*u.L)
    37.324192635827984 hour
    >>> T_stock(7*u.mL/u.s, 2*u.mg/u.L, "orange-yellow", 1*u.L)
    285.79443786361537 hour
    """
    return (V_stock / Q_stock_max(Q_plant, C, tubing_color)).to(u.hr)


def M_stock(Q_plant, C, tubing_color, V_stock):
    """The mass of the material required to reach the desired stock
    concentration.
    Parameters
    ----------
    Q_plant : float
        flow rate of the plant
    C : float
        desired concentration within the plant
    tubing_color : string
        color of the tubing to be used
    V_stock : float
        volume of the stock container
    Returns
    -------
    float
        mass of material to be added to the stock container
    Examples
    --------
    >>> M_stock(7*u.mL/u.s, 100*u.NTU, "yellow-blue", 1*u.L)
    159.89684125188708 gram
    """
    return (C_stock_max(Q_plant, C, tubing_color) * V_stock).to(u.g)


def V_super_stock(Q_plant, C, tubing_color, V_stock, C_super_stock):
    """The volume of super stock added to the stock container to reach the
    desired concentration within the plant.
    Parameters
    ----------
    Q_plant : float
        flow rate of the plant
    C : float
        desired concentration within the plant
    tubing_color : string
        color of the tubing to be used
    V_stock : float
        volume of the stock container
    C_super_stock : float
        concentration of the super stock to be diluted down to the
        stock solution
    Returns
    -------
    float
        volume of super stock to be added to the stock container
    Examples
    --------
    >>> V_super_stock(7*u.mL/u.s, 2*u.mg/u.L, "orange-yellow", 1*u.L, 69.4*u.g/u.L)
    207.55100386637196 milliliter
    """
    C_stock = C_stock_max(Q_plant, C, tubing_color)
    return (V_stock * C_stock / C_super_stock).to(u.mL)


def Q_water(Q_plant, C_clay, C_pacl_min, tubing_clay, tubing_pacl):
    """This function calculates the required flow rate for water from the tap
    for the experiment.
    Parameters
    ----------
    Q_plant : float
        flow rate of the plant
    C_clay : float
        concentration of clay to be added, i.e. the desired influent turbidity
    C_pacl_max : float
        minimum coagulant dose of the mixed water in the flocculator
    tubing_clay
        color of the tubing to be used for the clay stock
    tubing_clay
        color of the tubing to be used for the PACL stock
    Returns
    -------
    float
        required flow rate for water for the experiment if it were coming from
        a tap
    Examples
    --------
    >>> Q_water(7*u.mL/u.s, 100*u.NTU, 0.2*u.mg/u.L, "yellow-blue", "orange-yellow")
    419.49514512465606 milliliter/minute
    """
    return (Q_plant - Q_stock_max(Q_plant, C_clay, tubing_clay) -
            Q_stock_max(Q_plant, C_pacl_max, tubing_pacl)).to(u.mL/u.min)


def pump_rpm(Q, tubing_color):
    """This function calculates the RPMs required for a given flow rate and
    tube color.
    Parameters
    ----------
    Q : float
        desired flow rate
    tubing_color
        color of the tubing to be used
    Returns
    -------
    float
        revolutions per minute to set the pump to for the desired flow rate
    Examples
    --------
    >>> pump_rpm(0.01*u.mL/u.s, "yellow-blue")
    4.031012804669423 rev/minute
    """
    flow_per_rev = volPerRev_small(ID_colored_tube(tubing_color))
    return (Q / flow_per_rev).to(u.rev/u.min)
