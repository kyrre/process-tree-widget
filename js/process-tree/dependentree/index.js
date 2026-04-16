/*!
 *
 * Copyright 2022 Square Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

import * as clone from './clone';
import * as constructor from './constructor';
import * as addEntities from './add-entities';
import * as helpers from './helpers';
import * as mouse from './mouse';
import * as options from './options';
import * as text from './text';
import * as treeHelpers from './tree-helpers';
import * as setTree from './set-tree';
import * as update from './update';
import * as validate from './validate';


class DependenTree {
  constructor(elementSelectorString, userOptions) {
    this._constructor(elementSelectorString, userOptions);

    // default class properties, declared here to ensure these are new
    // objects in memory every time a new class instance is created
    this.nodeId = 0;
    this.upstream = {};
    this.downstream = {};
    this.missingEntities = [];
    this.dupDeps = [];
    this.keysMemo = {};
    this.clones = [];
    this.selectedNode = null;
  }
};


Object.assign(
  DependenTree.prototype,
  clone,
  constructor,
  addEntities,
  helpers,
  mouse,
  options,
  text,
  treeHelpers,
  setTree,
  update,
  validate,
);

export default DependenTree;