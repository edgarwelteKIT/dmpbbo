/**
 * @file   from_jsonpickle.hpp
 * @author Freek Stulp
 *
 * This file is part of DmpBbo, a set of libraries and programs for the 
 * black-box optimization of dynamical movement primitives.
 * Copyright (C) 2022 Freek Stulp
 * 
 * DmpBbo is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 * 
 * DmpBbo is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with DmpBbo.  If not, see <http://www.gnu.org/licenses/>. 
 */

#ifndef _FA_FROM_JSONPICKLE_H_
#define _FA_FROM_JSONPICKLE_H_

#include <nlohmann/json_fwd.hpp>


/** @ingroup FunctionApproximators
 */

 
namespace DmpBbo {

// Forward declaration
class FunctionApproximator;

class FunctionApproximatorFactory {

public:
  static void from_jsonpickle(const nlohmann::json& json, FunctionApproximator*& fa);

};

}

#endif // _FA_FROM_JSONPICKLE_H_