# context
i want to refactor a react file to make it shorter.
I do not want to change any html related logic

# rules
go over the file, and see what logic or interfaces we can extract to other files.:
we only extract pure logic and interfaces!!
for example, we DO NOT move 
we search for relevant files that can accomodate the logic, or we create new files

# example
example: 
1.  somefile.ts, public myMethod(...){<code>} to
    somefile.ts public myMethod(...){<call_to_someNewFile.ts.myMethod(...)>}
2. somefile.ts, const myMethod = (...){<code>} to
    somefile.ts const myMethod = (...){<call_to_someNewFile.ts.myMethod(...)>}

# what not to do
  extract:
     `useEffect(() => {
    // Sync certain graph filter states with main filters
  }, [graphFilterState.showCashEvents, ...]);` 
  to a new file

  instead we only move the inside `// Sync certain graph filter states with main filters`

  we DO NOT extract components    


# output
recommend what to extract
list by groups
summary of LOC saved, and LOCs in each new moved position
