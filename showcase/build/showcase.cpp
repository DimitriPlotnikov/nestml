/*
 *  showcase.cpp
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

// Includes from nestkernel:
#include "connection_manager_impl.h"
#include "connector_model_impl.h"
#include "dynamicloader.h"
#include "exceptions.h"
#include "genericmodel_impl.h"
#include "kernel_manager.h"
#include "model.h"
#include "model_manager_impl.h"
#include "nestmodule.h"
#include "target_identifier.h"

// Includes from sli:
#include "booldatum.h"
#include "integerdatum.h"
#include "sliexceptions.h"
#include "tokenarray.h"

// include headers with your own stuff
#include "showcase.h"

#include "ht_neuron_nestml.h"
#include "iaf_cond_alpha_implicit.h"
#include "iaf_cond_alpha_neuron.h"
#include "iaf_psc_alpha_multisynapse_neuron.h"
#include "iaf_psc_alpha_neuron.h"
// -- Interface to dynamic module loader ---------------------------------------

/*
 * There are three scenarios, in which MyModule can be loaded by NEST:
 *
 * 1) When loading your module with `Install`, the dynamic module loader must
 * be able to find your module. You make the module known to the loader by
 * defining an instance of your module class in global scope. (LTX_MODULE is
 * defined) This instance must have the name
 *
 * <modulename>_LTX_mod
 *
 * The dynamicloader can then load modulename and search for symbol "mod" in it.
 *
 * 2) When you link the library dynamically with NEST during compilation, a new
 * object has to be created. In the constructor the DynamicLoaderModule will
 * register your module. (LINKED_MODULE is defined)
 *
 * 3) When you link the library statically with NEST during compilation, the
 * registration will take place in the file `static_modules.h`, which is
 * generated by cmake.
 */
#if defined(LTX_MODULE) | defined(LINKED_MODULE)
showcase showcase_LTX_mod;
#endif

// -- DynModule functions ------------------------------------------------------

showcase::showcase() {
#ifdef LINKED_MODULE
  // register this module at the dynamic loader
  // this is needed to allow for linking in this module at compile time
  // all registered modules will be initialized by the main app's dynamic loader
  nest::DynamicLoaderModule::registerLinkedModule(this);
#endif
}

showcase::~showcase() {}

const std::string showcase::name(void) const {
  return std::string("showcase"); // Return name of the module
}

const std::string showcase::commandstring(void) const {
  // Instruct the interpreter to load showcase-init.sli
  return std::string("(showcase-init) run");
}

//-------------------------------------------------------------------------------------
void showcase::init(SLIInterpreter *i) {
  nest::kernel().model_manager.register_node_model<iaf_cond_alpha_implicit>(
      "iaf_cond_alpha_implicit");
  nest::kernel().model_manager.register_node_model<iaf_psc_alpha_neuron>(
      "iaf_psc_alpha_neuron");
  nest::kernel().model_manager.register_node_model<iaf_cond_alpha_neuron>(
      "iaf_cond_alpha_neuron");
  nest::kernel().model_manager.register_node_model<ht_neuron_nestml>(
      "ht_neuron_nestml");
  nest::kernel()
      .model_manager.register_node_model<iaf_psc_alpha_multisynapse_neuron>(
          "iaf_psc_alpha_multisynapse_neuron");
} // showcase::init()