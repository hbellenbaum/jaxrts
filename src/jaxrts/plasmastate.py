from .units import ureg, Quantity
from typing import List
import numpy as np
import logging
import jpu
from jax import numpy as jnp

from .elements import Element
from .setup import Setup

logger = logging.getLogger(__name__)


class PlasmaState:

    def __init__(
        self,
        ions: List[Element],
        Z_free: List | Quantity,
        density_fractions: List | float,
        mass_density: List | Quantity,
        T_e: List | Quantity,
        T_i: List | Quantity | None = None,
    ):

        assert (
            (len(ions) == len(Z_free))
            and (len(ions) == len(density_fractions))
            and (len(ions) == len(mass_density))
            and (len(ions) == len(T_e))
        ), "WARNING: Input parameters should be the same shape as <ions>!"
        if T_i is not None:
            assert len(ions) == len(
                T_i
            ), "WARNING: Input parameters should be the same shape as <ions>!"

        self.ions = ions
        self.nions = len(ions)

        # Define charge configuration
        self.Z_free = Z_free

        self.density_fractions = density_fractions
        self.mass_density = mass_density

        self.T_e = T_e
        self.T_i = T_i if T_i else T_e

        self.models = {}

    def __getitem__(self, key):
        return self.models[key]

    def __setitem__(self, key, model_class):
        self.models[key] = model_class(self)

    @property
    def Z_A(self) -> jnp.ndarray:
        """
        The atomic number of the atom-species.
        """
        return jnp.array([i.Z for i in self.ions])

    @property
    def Z_core(self) -> jnp.ndarray:
        """
        The number of electrons still bound to the ion.
        """
        return self.Z_A - self.Z_free

    @property
    def atomic_masses(self) -> Quantity:
        """
        The atomic weight of the atoms.
        """
        return jnp.array(
            [i.atomic_mass.m_as(ureg.atomic_mass_constant) for i in self.ions]
        ) * (1 * ureg.atomic_mass_constant)

    @property
    def n_i(self):
        return (
            self.mass_density / self.atomic_masses
        ).to_base_units()

    @property
    def n_e(self):
        return (jpu.numpy.sum(self.n_i * self.Z_free)).to_base_units()

    @property
    def ee_coupling(self):
        d = (3 / (4 * np.pi * self.n_e)) ** (1.0 / 3.0)

        return (
            (1 * ureg.elementary_charge) ** 2
            / (
                4
                * np.pi
                * (1 * ureg.vacuum_permittivity)
                * (1 * ureg.boltzmann_constant)
                * self.T_e
                * d
            )
        ).to_base_units()


    @property
    def ii_coupling(self):
        pass

    def db_wavelength(self, kind: List | str):

        wavelengths = []

        if isinstance(kind, str):
            kind = [kind]
        for par in kind:
            assert (par == "e-") or (
                par in self.ions
            ), "Kind must be one of the ion species or an electron (e-)!"
            if par == "e-":
                wavelengths.append(
                    (
                        (1 * ureg.planck_constant)
                        / jpu.numpy.sqrt(
                            2.0
                            * np.pi
                            * 1
                            * ureg.electron_mass
                            * 1
                            * ureg.boltzmann_constant
                            * self.T_e
                        )
                    ).to_base_units()
                )
            else:
                wavelengths.append(
                    (
                        (1 * ureg.planck_constant)
                        / jpu.numpy.sqrt(
                            2.0
                            * np.pi
                            * 1
                            * self.atomic_masses[
                                np.argwhere(np.array(self.ions == par))
                            ]
                            * 1
                            * ureg.boltzmann_constant
                            * self.T_e
                        )
                    ).to_base_units()
                )

    def probe(self, setup: Setup) -> Quantity:
        ionic = self["ionic scattering"].evaluate(setup)
        free_free = self["free-free scattering"].evaluate(setup)
        bound_free = self["bound-free scattering"].evaluate(setup)
        free_bound = self["free-bound scattering"].evaluate(setup)

        return ionic + free_free + bound_free + free_bound
