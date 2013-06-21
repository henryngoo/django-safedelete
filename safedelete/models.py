from django.db import models
from .managers import safedelete_manager_factory
from .utils import related_objects, HARD_DELETE, SOFT_DELETE, SOFT_DELETE_CASCADE, HARD_DELETE_NOCASCADE, DELETED_INVISIBLE, DELETED_VISIBLE_BY_PK



def safedelete_mixin_factory(
            policy,
            visibility=DELETED_INVISIBLE,
            manager_superclass=models.Manager
        ):

    assert policy in (HARD_DELETE, SOFT_DELETE, SOFT_DELETE_CASCADE, HARD_DELETE_NOCASCADE)

    class Model(models.Model):
        """
        This base model provides date fields and functionality to enable logical
        delete functionality in derived models.
        """
        
        deleted = models.BooleanField(default=False)
        
        objects = safedelete_manager_factory(manager_superclass, visibility)()
        
        def save(self, keep_deleted=False, **kwargs):
            if not keep_deleted:
                self.deleted = False
            super(Model, self).save(**kwargs)

        def undelete(self):
            assert self.deleted
            self.date_removed = False
            self.save(keep_deleted=True)

        def delete(self, force_policy=None, **kwargs):
            current_policy = policy if force_policy is None else force_policy

            if current_policy in (SOFT_DELETE, SOFT_DELETE_CASCADE):

                # Only soft-delete the object, marking it as deleted.
                self.deleted = True
                super(Model, self).save(**kwargs)

                if current_policy == SOFT_DELETE_CASCADE:
                    for obj in related_objects(self):
                        obj.delete(force_policy=SOFT_DELETE)

            elif current_policy == HARD_DELETE:

                # Normally hard-delete the object.
                super(Model, self).delete()

            elif current_policy == HARD_DELETE_NOCASCADE:

                # Hard-delete the object only if nothing would be deleted with it

                if sum(1 for _ in related_objects(self)) > 0:
                    self.delete(force_policy=SOFT_DELETE, **kwargs)
                else:
                    self.delete(force_policy=HARD_DELETE, **kwargs)

            else:
                raise ValueError("Invalid policy for deletion.")

        
        class Meta:
            abstract = True

    return Model


SoftDeleteMixin = safedelete_mixin_factory(SOFT_DELETE)