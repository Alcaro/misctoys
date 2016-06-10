Visual Studio laziness bugs
===========================

All were found in Visual Studio 2015 Update 1 or Update 2.

```csharp
using System.Threading.Tasks;

class Task { }
class foo
{
    async Task bar() { } // Error: The return type of an async method must be void, Task or Task<T>
                         // But the return type is 'Task'.
}
```

```csharp
class Foo
{
    void Bar()
    {
        int a = 0;
        long b = (long)a << 32 | (long)a; // Cast is redundant.
        long c = (long)a << 32 | a; // Bitwise-or operator used on a sign extended operand;
                                    // consider casting to a smaller unsigned type first
    }
}
```

```csharp
class Foo {} // Rename this to Bar. Visual Studio will offer to replace all other references to Foo - but there are none.
```

```csharp
namespace Foo
{
    public class Bar<T> { }
    public static class Util
    {
        public static T Baz<T>(this Bar<T> foo, T bar)
        {
            return default(T);
        }

        public static T Quux<T>(this Bar<T> foo)
        {
            // Argument 2: cannot convert from '<null>' to 'T'
            // Suggested Quick Fix: Add 'using Foo;'. This does, of course, not help; I'm surprised it's not marked unused.
            // Another Quick Fix is adding Bar.Baz, which helps slightly more.
            return foo.Baz(null);
        }
    }
}
```

```csharp
namespace Foo
{
    public int Bar()
    {
        // Put the cursor on Baz and poke Ctrl-Period (Quick Fixes).
        // Result:
        // It offers four quick fixes:
        //  Generate property '<invalid-global-code>.Baz'
        //  Generate field 'Baz' in '<invalid-global-code>'
        //  Generate read-only field 'Baz' in '<invalid-global-code>'
        //  Generate local 'Baz'
        // and then opens a warning bar on top of Visual Studio saying
        //  "'GenerateVariableCodeFixProvider' encountered an error and has been disabled"
        // After that, similar Quick Fixes are no longer available until I press Enable.
        // Expected result: Don't crash. And maybe don't use angle brackets to remind me that functions go in classes.
        return Baz;
    }
}
```

```csharp
using System.Threading.Tasks;

class AwaitNull
{
    class HasAsyncFunction
    {
        // throws an irrelevant 'function runs synchronously' warning
        public async Task<object> test1() { return new object(); }
    }
    static async Task<object> test2()
    {
        HasAsyncFunction test3 = null;
        //Expected result: Returns null, or at least a compiler warning
        //Actual result: NullReferenceException (wrapped in an AggregateException)
        return await test3?.test1();
    }

    static void Main(string[] args)
    {
        var test4 = test2().Result;
    }
}
```

```csharp
//FIXME: Put this file in two projects in the same solution, then look at the Task List.
//Expected: One entry pointing to both projects, the same way errors do.
//Actual: Two entries, one for each project. Despite both going to the same place.
//The bug is also reproducible with Find All References.
```

```csharp
class Program
{
    static void Main(string[] args)
    {
        {
            int foo = 42;
        }
        {
            string foo = "Test";
            //Put a breakpoint here, or that brace down there. VS shows the values of local
            // variables if you hover the mouse on them; do that to 'int foo' up there.
            //Expected results: 'int foo' is out of scope and no longer has a value.
            // Alternatively, show the value it last had (42), but that's overkill.
            //Actual: It's got the value 'Test'. Integers don't have that value.
        }
    }
}
```
