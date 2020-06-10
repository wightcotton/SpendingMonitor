from app.models import User, CategoryState, StateLookup
from app import db


class CategoryStateAccess(object):
    def __init__(self, user_id):
        self.user_id = user_id

    # CATEGORY STATE

    def set_current_state(self, category, state_id):
        category_state = CategoryState(user_id=self.user_id, category=category, state=state_id)
        db.session.add(category_state)
        db.session.commit()

    def get_current_state_id(self, category):
        csa_record = CategoryState.query.filter_by(user_id=self.user_id, category=category).order_by(
            CategoryState.timestamp.desc()).first()
        if csa_record:
            return csa_record.state
        else:
            None

    def get_categories_current_state(self):
        ret = []
        for cat in db.session.query(CategoryState.category).distinct().all():
            state = db.session.query(StateLookup).filter(StateLookup.id == self.get_current_state_id(cat)).first().state
            ret.append((cat[0], state))
        return ret

    def get_category_state_info(self, category):
        return db.session.query(CategoryState, StateLookup). \
            filter(CategoryState.state == StateLookup.id). \
            filter(CategoryState.category == category).order_by(CategoryState.timestamp.desc()).all()

    # end CATEGORY STATE

    # STATE LOOKUP

    def add_lookup_state(self, state=None, desc=None):
        state_record = StateLookup(user_id=self.user_id, state=state, description=desc)
        db.session.add(state_record)
        db.session.commit()

    def set_lookup_states(self, list_of_states):
        for state in list_of_states:
            state_record = StateLookup(user_id=self.user_id, state=state, description='initial load')
            db.session.add(state_record)
            db.session.commit()

    def get_lookup_states(self):
        return StateLookup.query.filter_by(user_id=self.user_id).all()

    def delete_lookup_states(self, state_id_list=None):
        if state_id_list is None:
            return 'Nothing to delete'
        for k in state_id_list:
            state_record = StateLookup.query.filter_by(user_id=self.user_id, id=k).first()
            db.session.delete(state_record)
            db.session.commit()
        return 'Completed'

    # end STATE LOOKUP
