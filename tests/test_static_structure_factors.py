import pathlib

import pytest
import numpy as onp
import jaxrts
from jax import numpy as jnp

ureg = jaxrts.ureg


@pytest.mark.skip(
    reason="Re-producing figures from Arkhipov.1998 is not possible"
)
def test_arkhipov_static_structure_factors_literature():
    """
    Test the calculations against the data displayed in Fig. 3 and Fig. 4
    of :cite:`Arkhipov.1998`
    """
    r_s = 0.1
    Z_f = 1
    m_i = 1.0 * ureg.atomic_mass_constant
    a = r_s * ureg.a_0
    n_e = 3 / (4 * jnp.pi * a**3)

    for fig, gam in zip([3, 4], [0.1, 1]):
        data_dir = (
            pathlib.Path(__file__).parent / f"data/Arkhipov1998/Fig{fig}/"
        )
        ka_See, lit_See = onp.genfromtxt(
            data_dir / "S_ee.csv", delimiter=",", unpack=True
        )
        ka_Sei, lit_Sei = onp.genfromtxt(
            data_dir / "S_ei.csv", delimiter=",", unpack=True
        )
        k_See = ka_See / a
        k_Sei = ka_Sei / a

        T_e = ureg.elementary_charge**2 / (
            (4 * jnp.pi * ureg.vacuum_permittivity)
            * ureg.boltzmann_constant
            * gam
            * a
        )

        calc_See = jaxrts.static_structure_factors.S_ee_AD(
            k_See, T_e, T_e, n_e, m_i, Z_f
        ).m_as(ureg.dimensionless)
        calc_Sei = jaxrts.static_structure_factors.S_ei_AD(
            k_Sei, T_e, T_e, n_e, m_i, Z_f
        ).m_as(ureg.dimensionless)

        assert jnp.max(jnp.abs(lit_See - calc_See)) < 0.05
        assert jnp.max(jnp.abs(lit_Sei - calc_Sei)) < 0.05


def test_arkhipov_electron_electron_pair_correlation_function_literature():
    """
    Test the calculations against the data displayed in Fig. 2 of
    :cite:`Arkhipov.2000`
    """
    r_s = 0.1
    Z_f = 1
    m_i = 1.0 * ureg.atomic_mass_constant
    a = r_s * ureg.a_0
    n_e = 3 / (4 * jnp.pi * a**3)
    gam = 0.3
    T_e = ureg.elementary_charge**2 / (
        (4 * jnp.pi * ureg.vacuum_permittivity)
        * ureg.boltzmann_constant
        * gam
        * a
    )

    # Load the data
    data_dir = pathlib.Path(__file__).parent / "data/Arkhipov2000/"
    R_over_a_gee, lit_gee = onp.genfromtxt(
        data_dir / "Fig2.csv", delimiter=",", unpack=True
    )
    R_gee = R_over_a_gee * a
    calc_gee = jaxrts.static_structure_factors.g_ee_ABD(
        R_gee, T_e, T_e, n_e, m_i, Z_f
    ).m_as(ureg.dimensionless)

    assert jnp.max(jnp.abs(lit_gee - calc_gee)) < 0.015
    assert jnp.mean(jnp.abs(lit_gee - calc_gee)) < 0.003


def test_gregori2006_figure_1_reproduction_Sii():
    """
    Test if the Sii part of Fig.1 of :cite:`Gregori.2006` can be reproduced,
    i.e., if this part for calculating W_R with non-idential electron and ion
    temperatures is correct.
    """
    data_dir = pathlib.Path(__file__).parent / "data/Gregori2006/Fig1/Sii"

    # Set up the parameters
    m_i = jaxrts.Element("Be").atomic_mass
    n_e = ureg("2.5e23/cm³")
    T_e = ureg("20eV") / (1 * ureg.k_B)
    Z_f = 2

    T_e_prime = jaxrts.static_structure_factors.T_cf_Greg(T_e, n_e)
    T_D = jaxrts.static_structure_factors.T_Debye_Bohm_Staver(
        T_e_prime, n_e, m_i, Z_f
    )
    k_De = jaxrts.static_structure_factors._k_D_AD(T_e_prime, n_e)

    for f in data_dir.glob("*.csv"):
        k_over_kDe, lit_Sii = onp.genfromtxt(f, delimiter=",", unpack=True)
        k = k_over_kDe * k_De
        T_i_over_T_e = float(f.stem)
        T_i = T_e * T_i_over_T_e
        T_i_prime = jaxrts.static_structure_factors.T_i_eff_Greg(T_i, T_D)

        calc_Sii = jaxrts.static_structure_factors.S_ii_AD(
            k, T_e_prime, T_i_prime, n_e, m_i, Z_f
        )
        assert (
            jnp.max(jnp.abs(lit_Sii - calc_Sii.m_as(ureg.dimensionless)))
            < 1e-2
        )


def test_gregori2006_figure_1_reproduction_Sei():
    """
    Test if the Sei part of Fig.1 of :cite:`Gregori.2006` can be reproduced,
    i.e., if this part for calculating W_R with non-idential electron and ion
    temperatures is correct.
    """
    data_dir = pathlib.Path(__file__).parent / "data/Gregori2006/Fig1/Sei"

    # Set up the parameters
    m_i = jaxrts.Element("Be").atomic_mass
    n_e = ureg("2.5e23/cm³")
    T_e = ureg("20eV") / (1 * ureg.k_B)
    Z_f = 2

    T_e_prime = jaxrts.static_structure_factors.T_cf_Greg(T_e, n_e)
    T_D = jaxrts.static_structure_factors.T_Debye_Bohm_Staver(
        T_e_prime, n_e, m_i, Z_f
    )
    k_De = jaxrts.static_structure_factors._k_D_AD(T_e_prime, n_e)

    import matplotlib.pyplot as plt

    for f in data_dir.glob("*.csv"):
        k_over_kDe, lit_Sei = onp.genfromtxt(f, delimiter=",", unpack=True)
        k = k_over_kDe * k_De
        T_i_over_T_e = float(f.stem)
        T_i = T_e * T_i_over_T_e
        T_i_prime = jaxrts.static_structure_factors.T_i_eff_Greg(T_i, T_D)

        calc_Sei = jaxrts.static_structure_factors.S_ei_AD(
            k, T_e_prime, T_i_prime, n_e, m_i, Z_f
        )
        assert (
            jnp.max(jnp.abs(lit_Sei - calc_Sei.m_as(ureg.dimensionless)))
            < 1e-2
        )


def test_gregori2006_figure_1_reproduction_See():
    """
    Test if the See part of Fig.1 of :cite:`Gregori.2006` can be reproduced,
    i.e., if this part for calculating W_R with non-idential electron and ion
    temperatures is correct.
    """
    data_dir = pathlib.Path(__file__).parent / "data/Gregori2006/Fig1/See"

    # Set up the parameters
    m_i = jaxrts.Element("Be").atomic_mass
    n_e = ureg("2.5e23/cm³")
    T_e = ureg("20eV") / (1 * ureg.k_B)
    Z_f = 2

    T_e_prime = jaxrts.static_structure_factors.T_cf_Greg(T_e, n_e)
    T_D = jaxrts.static_structure_factors.T_Debye_Bohm_Staver(
        T_e_prime, n_e, m_i, Z_f
    )
    k_De = jaxrts.static_structure_factors._k_D_AD(T_e_prime, n_e)

    for f in data_dir.glob("*.csv"):
        k_over_kDe, lit_See = onp.genfromtxt(f, delimiter=",", unpack=True)
        k = k_over_kDe * k_De
        T_i_over_T_e = float(f.stem)
        T_i = T_e * T_i_over_T_e
        T_i_prime = jaxrts.static_structure_factors.T_i_eff_Greg(T_i, T_D)

        calc_See = jaxrts.static_structure_factors.S_ee_AD(
            k, T_e_prime, T_i_prime, n_e, m_i, Z_f
        )

        assert (
            jnp.max(jnp.abs(lit_See - calc_See.m_as(ureg.dimensionless)))
            < 1e-2
        )


def test_gregori2006_figure_1_reproduction_q():
    """
    Test if the q part of Fig.1 of :cite:`Gregori.2006` can be reproduced,
    i.e., if this part for calculating W_R with non-idential electron and ion
    temperatures is correct.
    """
    data_dir = pathlib.Path(__file__).parent / "data/Gregori2006/Fig1/q"

    # Set up the parameters
    m_i = jaxrts.Element("Be").atomic_mass
    n_e = ureg("2.5e23/cm³")
    T_e = ureg("20eV") / (1 * ureg.k_B)
    Z_f = 2

    T_e_prime = jaxrts.static_structure_factors.T_cf_Greg(T_e, n_e)
    T_D = jaxrts.static_structure_factors.T_Debye_Bohm_Staver(
        T_e_prime, n_e, m_i, Z_f
    )
    k_De = jaxrts.static_structure_factors._k_D_AD(T_e_prime, n_e)

    for f in data_dir.glob("*.csv"):
        k_over_kDe, lit_q = onp.genfromtxt(f, delimiter=",", unpack=True)
        k = k_over_kDe * k_De
        T_i_over_T_e = float(f.stem)
        T_i = T_e * T_i_over_T_e
        T_i_prime = jaxrts.static_structure_factors.T_i_eff_Greg(T_i, T_D)

        calc_Sei = jaxrts.static_structure_factors.S_ei_AD(
            k, T_e_prime, T_i_prime, n_e, m_i, Z_f
        )
        calc_Sii = jaxrts.static_structure_factors.S_ii_AD(
            k, T_e_prime, T_i_prime, n_e, m_i, Z_f
        )

        # This is the q calculated by Gregori.2006
        simple_q = jnp.sqrt(Z_f) * calc_Sei / calc_Sii
        # For comparison, also calculate the full q using e.g. Gregri 2003 and
        # assert that these results are not too diffrent.
        calc_q = jaxrts.ion_feature.q(k, m_i, n_e, T_e, T_i, Z_f)

        assert (
            jnp.max(jnp.abs(lit_q - simple_q.m_as(ureg.dimensionless))) < 2e-2
        )

        # Allow more deviations for the comparison of two definitions for q.
        assert (
            jnp.max(
                jnp.abs(
                    simple_q.m_as(ureg.dimensionless)
                    - calc_q.m_as(ureg.dimensionless)
                )
            )
            < 1e-1
        )
        assert (
            jnp.mean(
                jnp.abs(
                    simple_q.m_as(ureg.dimensionless)
                    - calc_q.m_as(ureg.dimensionless)
                )
            )
            < 3e-2
        )
