from typing import List
from decaf_ast import ClassRecord, DependencyTree
from decaf_config import LINE
from decaf_util import Counter


def resolve_sizes_and_offsets(classes: List["ClassRecord"]) -> int:
    """
    This method takes in a bunch of type-verified classes.
    For each class given in the provided order, it will compute the required instance size
    For each field of a class, it will also compute their offsets in parallel.
    Returns the number of static slots needed.
    """
    # this generator will give me an unique offset for static fields
    static_offset_gen = Counter(0)
    
    for class_rec in classes:
        # obtain the super class record, if any
        super_class_rec: "ClassRecord" = None
        if class_rec.super_class_name != None:
            rec = DependencyTree.get_class_record(class_rec.super_class_name)
            if rec == None:
                raise Exception("illegal program state - super class cannot be None after type checking")
            super_class_rec = rec
            
        # determine the min slots needed to fit all members of super class, if any
        super_size = 0 if super_class_rec == None else super_class_rec.size
        
        # this generator will give me an unique offset for an instance field
        # it takes into account that offset begins at the end of super class slots
        instance_offset_gen = Counter(super_size)
        
        # determine the offsets of each field in class
        for field_rec in class_rec.fields:
            if field_rec.applicability == "static":
                field_rec.offset = static_offset_gen.next()
            else:
                field_rec.offset = instance_offset_gen.next()
        
        # compute current class size after dealing with all fields
        class_rec.size = instance_offset_gen.next()
    
    return static_offset_gen.next()

def print_class_offsets(classes: List["ClassRecord"]):
    """
    Takes in a bunch of type-checked classes that have already been assigned offsets.
    Prints them out in a readable manner.
    """
    print(LINE)
    for class_rec in classes:
        print(f"Class Name: {class_rec.name}")
        print(f"Superclass Name: {class_rec.super_class_name}")
        print(f"Instance Size: {class_rec.size}")
        
        print("Fields:")
        for field_rec in class_rec.fields:
            print(f"[OFFSET={field_rec.offset}] {repr(field_rec)}")
            
        print(LINE)
