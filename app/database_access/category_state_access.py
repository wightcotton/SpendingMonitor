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

    def get_current_state_id(self, category): #-> return current state id for a category
        cs_record = CategoryState.query.filter_by(user_id=self.user_id, category=category).order_by(
            CategoryState.timestamp.desc()).first()
        if cs_record:
            return cs_record.state
        else:
            return 'include'

    def get_current_state(self, category): #-> return current state name for a category
        current_state_record = CategoryState.query.filter_by(user_id=self.user_id, category=category)\
            .order_by(CategoryState.timestamp.desc()).first()
        if current_state_record:
            return self.get_lookup_state(current_state_record.state)
        else:
            return 'include'

    def get_categories_current_state(self): #-> [[state, [category, category], [state, [category, category]]
        ret = []
        for csr in CategoryState.query.filter_by(user_id=self.user_id).distinct().all():
            cat = csr.category
            state = db.session.query(StateLookup).filter(StateLookup.id == self.get_current_state_id(cat)).first().state
            ret.append((cat[0], state))
        return ret

    def get_categories_by_current_state(self):
        ret_dict = {}
        for t in self.get_categories_current_state():
            if t[1] in ret_dict:
                ret_dict[t[1]].append(t[0])
            else:
                ret_dict[t[1]] = [t[0]]
        return [[key, value] for key, value in ret_dict.items()]

    def get_categories_current_state_for(self, state): #-> list of categores for a state
        for item in self.get_categories_by_current_state():
            if item[0] == state:
                return item[1]
        return []

    def get_category_state_info(self, category): #-> list of all cat state records for a category
        return db.session.query(CategoryState, StateLookup). \
            filter(CategoryState.state == StateLookup.id). \
            filter(CategoryState.category == category).order_by(CategoryState.timestamp.desc()).all()

    def delete_category_states(self, category=None, state_id=None):
        category_state_records = []
        if category:
            category_state_records = CategoryState.query.filter_by(user_id=self.user_id, category=category).all()
        elif state_id:
            category_state_records = CategoryState.query.filter_by(user_id=self.user_id, state=state_id).all()
        for r in category_state_records:
            db.session.delete(r)
        db.session.commit()

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

    def set_default_lookup_states(self):
        self.set_lookup_states(['examine', 'fix', 'ignore', 'include'])

    def get_lookup_states(self): #-> list of all records from lookup table
        return StateLookup.query.filter_by(user_id=self.user_id).all()

    def get_lookup_state(self, state_id): #-> state name
        return StateLookup.query.filter(StateLookup.id == state_id).first().state

    def delete_lookup_states(self, state_id_list=None):
        if state_id_list is None:
            return 'Nothing to delete'
        for k in state_id_list:
            self.delete_category_states(state_id=k)
            state_record = StateLookup.query.filter_by(user_id=self.user_id, id=k).first()
            db.session.delete(state_record)
            db.session.commit()
        return 'Completed'

    # end STATE LOOKUP
