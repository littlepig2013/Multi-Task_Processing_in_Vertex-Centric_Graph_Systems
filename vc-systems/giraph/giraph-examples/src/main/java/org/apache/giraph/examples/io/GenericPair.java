package org.apache.giraph.examples.io;
public class GenericPair<E extends Object, F extends Object> {  
    private E first;  
    private F second;  
      
    public GenericPair(){  
          
    }  
      
    public GenericPair(E first1, F second1){
        first=first1;
        second = second1;
    }
    public E getFirst() {  
        return first;  
    }  
    public void setFirst(E first) {  
        this.first = first;  
    }  
    public F getSecond() {  
        return second;  
    }  
    public void setSecond(F second) {  
        this.second = second;  
    }  
      
      
}  