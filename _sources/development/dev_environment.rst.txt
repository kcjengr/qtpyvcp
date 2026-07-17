Development Guide
^^^^^^^^^^^^^^^^^

If you are new to working with git this should get you going.


Creating a Local Checkout
=========================

If you want to make changes to QtPyVCP the first step is to create your own fork
of the repository. This allows you to create feature branches and push changes
to your personal fork so that others can view and test them, without you having
to worry about messing anything up in the main repository. It is easy to fork,
but here is a `quick tutorial <https://help.github.com/articles/fork-a-repo>`_
if needed.

Once your fork is created you can clone it to your local machine.

.. code:: sh

   $ git clone https://github.com/YOUR-USERNAME/REPOSITORY.git

Now that you have a copy of the repository, create a branch for the feature or
bug you would like to work on.

.. code:: sh

   $ git checkout -b my-feature

   $ git status
   On branch my-feature
   nothing to commit, working tree clean

.. admonition:: ProTip

    I highly recommended a GUI git client called `GitKraken <https://www.gitkraken.com/>`_.
    It makes even complicated git tasks as simple as a few clicks, and the
    visual commit history is very helpful.


Merging Changes
===============

Once you are happy with your code, ``push`` it back to your fork on GitHub.

.. code:: sh

   $ git push origin my-feature

You should now be able to create a Pull Request back to the original repository.
Once the changes are checked and reviewed the Pull Request can be merged.


Syncing your Local Checkout
===========================

Inevitably, changes to the upstream repository will occur and you will need to
update your local checkout to reflect those. The first step is to make your
local checkout aware of the upstream repository:

.. code:: sh

   $ git remote add upstream https://github.com/kcjengr/qtpyvcp.git
   $ git remote -v
   origin   https://github.com/YOUR-USERNAME/qtpyvcp.git (fetch)
   origin   https://github.com/YOUR-USERNAME/qtpyvcp.git (push)
   upstream https://github.com/kcjengr/qtpyvcp.git (fetch)
   upstream https://github.com/kcjengr/qtpyvcp.git (push)

Now, you need to fetch any changes from the upstream repository. ``git fetch``
will grab the latest commits that were merged since you made your fork.

.. code:: sh

   $ git fetch upstream


Ideally you haven't made any changes to your ``master`` branch. So you should be
able to merge the latest ``master`` branch from the upstream repository without
concern. All you need to do is to switch to your ``master`` branch, and pull in
the changes from the upstream remote. It is usually a good idea to push any
changes back to your fork as well.

.. code:: sh

   $ git checkout master
   $ git pull upstream master
   $ git push origin master

Finally, you need to update your feature-branch to have the new changes. It is
best to use a ``git rebase`` to take the local changes, remove them temporarily,
pull the upstream changes, and then re-add the local changes on the
tip of the commit history. This avoids extraneous merge commits that clog the
commit history of the branch. A more in-depth discussion can be found `here
<https://www.atlassian.com/git/tutorials/merging-vs-rebasing>`__. This process
would look something look like this:

.. code:: sh

   $ git checkout my-feature
   $ git rebase upstream/master

.. warning::
   A rebase should not be done if you think that anyone else is also
   working on the branch. Rebasing re-writes the commit history so
   any other checkout of the same branch will have the old history
   so when they are eventually merged there will be duplicates of all
   the rebased commits. Kinda defeats the purpose of the rebase :)
